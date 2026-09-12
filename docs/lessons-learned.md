# Production lessons

This system ran in production against a real CRM, a real inbox, and real
external APIs for several months. These are the lessons that generalize
beyond this one project - client-identifying specifics are intentionally
left out.

## Pagination that silently caps results is worse than an API that errors

A CRM board API returned results a page at a time, and an early version of
the sync code only read the first page. The board itself had more items
than that page contained, so the system believed the board was smaller than
it really was - and re-processed contacts that were, in fact, already
present, because the dedup check never saw them. The fix wasn't "add a
warning"; it was to make the client's public method return the *complete*
paginated set always, so every caller downstream is written against a
complete list by construction and can't reintroduce the bug by forgetting
to page.

## A silent search-space exhaustion looks like "it's working, just slower"

Discovery yield collapsed over time when the search terms were too broad -
the same handful of already-known businesses kept surfacing on every run,
crowding out genuinely new results within the page limit. It didn't error,
it didn't look broken, it just quietly produced fewer new leads per day
than expected. The fix was structural: split one broad search into many
narrow ones (region x segment), so each individual query has a smaller,
faster-exhausted result set and the run as a whole keeps finding new
businesses instead of re-finding old ones.

## Distinguish "the call failed" from "the result is empty"

A failed external API call and a genuinely empty result must never look the
same to calling code. If they do, retry logic can't tell whether it's safe
to retry, and write logic can't tell whether it's safe to proceed - a
transient failure disguised as "zero records" can lead directly to
duplicate creation or a missed write.

## Human approval has to sit before the side effect, not after

It's tempting to log an AI-generated action and let a human review it
after the fact. That only works if reversal is free. For an outbound email,
it isn't - so approval has to gate the send itself, not audit it
afterward.

## A rejection should mean "stop," not "skip once"

Early cadence logic only skipped the specific draft that got rejected -
the contact could still re-enter the pipeline on the next stage. That's
the wrong default for a rejection: a human saying no to one email is almost
always a signal to stop entirely, not a signal to try again later with
different wording.

## Deployment verification is not optional for a background daemon

A process that runs unattended on a schedule can fail silently between
deploys if nothing confirms which commit is actually running, or if a
deploy step has an unrelated side effect (in one case, a deploy script
that also cleared the log directory, making the previous run's behavior
unrecoverable for debugging). A daemon needs an explicit, checkable record
of "what's running right now," separate from "what's in the repo."

## DRY_RUN has to be a parameter, not a global check buried downstream

Making every side-effecting call take an explicit `dry_run` argument (rather
than checking a global flag somewhere inside the client) means there's no
code path where a caller can forget the check - the check is part of the
function signature, not a convention someone has to remember to follow.

## Command surfaces need the same access control as the actions they trigger

A chat-based operator command (halt a contact, generate ad-hoc content) is
still a command that mutates state or costs money to run. If anyone in the
channel can invoke it, the "human in the loop" is anyone in the room, not
a specific accountable person - worth deciding deliberately, not by
default.
