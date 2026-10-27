# Routing rules

**Used by:** profile-update, before drafting any write.

Routing decides where a staged item goes: which part of the profile, and
whether it becomes a new entry, an addition to an existing one, a list item, or
nothing. It comes before any wording. A wrong route cannot be fixed by good
writing.

## Step 1: pull what already exists

Run:

```
python scripts/profile_slice.py related --item "<label>"
```

It prints every entry in the item's work role, plus entries in other roles that
share key words with what the item says the candidate did. When it says the
pull has more than one part, read every part with `--part N` before deciding.
Decide from this list, not from memory. Paste the full text of any entry you
name to the user; never cite one by ID alone.

## Step 2: pick one outcome

Exactly one of these, with a one- or two-line reason:

- **New entry.** Nothing pulled covers this piece of work. Name the entry type
  and the role it belongs to. For an EX entry, also name the topic group it
  joins: one of the `--- <label>` groups the pull shows for that role, or a new
  group with a proposed label. A new group needs the user's approval.
- **Addition to an existing entry.** An entry covers the work but under-states
  or mis-frames it, or a project needs a new or changed element. Name the entry.
- **List item.** The item is a named tool, product, or platform, not a piece of
  work. Name the list it goes under.
- **Duplicate.** The profile already carries it accurately. Nothing is written;
  the item is removed.
- **Retract.** The item should not go into the profile. This is the user's call
  only. Raise the doubt and take their decision; never propose it to clear a
  backlog.

## Structure tests

- **One home per piece of work.** When two roles overlap, file the work where
  most of its substance happened.
- **Split** an item that holds two kinds of work: leadership and hands-on work,
  a process and a technical component, or setting up roles and managing
  stakeholders. Each becomes its own entry.
- **Merge or skip** when the item repeats another entry's result. Add what is
  new to that entry instead.
- **A thin parent is fine.** A group parent can hold only a headline and the
  group's result; its children hold the activities.
- **Drop what the candidate cannot explain** if pressed. Log the removed ID in
  `inventory-ret.md`.

## Items this run leaves in the queue

- An item that belongs in the narratives document. Narrative writing rules come
  later; until then the item waits.
- An item that belongs in positioning. The user writes positioning by hand.

Say so plainly to the user and move to the next item.

## Ask instead of guessing

Ask the user, and wait, when a fact the entry needs is not in the item. Flag an
unverified fact in one line. Never fill a gap with an inference.
