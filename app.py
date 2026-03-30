import streamlit as st
from pawpal_system import Owner, Pet, Task, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")

# ── Session state: check before creating, never overwrite on re-run ───────────
# st.session_state acts like a dictionary that survives page refreshes.
# The "not in" guard means we only create the Owner once per session.
if "owner" not in st.session_state:
    st.session_state.owner = None

if "scheduler" not in st.session_state:
    st.session_state.scheduler = None

# ── 1. Owner & Pet info ───────────────────────────────────────────────────────
st.header("1. Owner & Pet Information")

col1, col2 = st.columns(2)
with col1:
    owner_name = st.text_input("Owner name", value="Jordan")
    owner_contact = st.text_input("Contact / phone (optional)", value="")
with col2:
    pet_name = st.text_input("Pet name", value="Mochi")
    species = st.selectbox("Species", ["cat", "dog", "bird", "rabbit", "other"])
    age = st.number_input("Pet age (years)", min_value=0, max_value=30, value=3)

if st.button("Save owner & pet"):
    # Build the objects and store the Owner in the vault — not just the Scheduler.
    owner = Owner(name=owner_name, contact=owner_contact)
    pet = Pet(name=pet_name, species=species, age=int(age))
    owner.add_pet(pet)
    st.session_state.owner = owner                      # persisted in session
    st.session_state.scheduler = Scheduler(owner=owner) # persisted in session
    st.success(f"Saved! Tracking {pet.name} the {pet.species} for {owner.name}.")

# Gate: nothing below runs until the vault has an Owner.
if st.session_state.owner is None:
    st.info("Fill in the form above and click **Save owner & pet** to get started.")
    st.stop()

# Retrieve live references from the vault — same objects, not new ones.
owner: Owner = st.session_state.owner
scheduler: Scheduler = st.session_state.scheduler

st.divider()

# ── 2. Add tasks ──────────────────────────────────────────────────────────────
st.header("2. Add Care Tasks")

pet_names = [p.name for p in owner.pets]
col1, col2, col3, col4 = st.columns(4)
with col1:
    target_pet = st.selectbox("For pet", pet_names)
with col2:
    description = st.text_input("Task description", value="Morning walk")
with col3:
    time = st.text_input("Time", value="08:00")
with col4:
    priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)

col5, col6 = st.columns(2)
with col5:
    frequency = st.selectbox("Frequency", ["daily", "twice daily", "weekly", "once", "as needed"])
with col6:
    st.write("")  # spacer

if st.button("Add task"):
    task = Task(
        description=description,
        time=time,
        frequency=frequency,
        priority=priority,
    )
    scheduler.add_task(pet_name=target_pet, task=task)
    st.success(f"Added '{description}' for {target_pet}.")

st.divider()

# ── 3. Schedule view & completion tracking ────────────────────────────────────
st.header("3. Daily Schedule")

# Conflict detection banner
conflicts = scheduler.detect_conflicts()
for c in conflicts:
    st.warning(
        f"Schedule conflict for **{c['pet']}** on {c['due_date']} at {c['time']}: "
        + " vs ".join(f"'{t}'" for t in c["tasks"])
    )

plan = scheduler.daily_plan()

if not plan:
    st.info("No pending tasks — add some above.")
else:
    st.write(f"**{len(plan)} task(s) remaining today**")
    st.table(plan)

    st.subheader("Mark a task complete")
    pending = scheduler.get_pending_tasks()
    if pending:
        options = {f"{pet.name} — {task.description}": (pet.name, task.description)
                   for pet, task in pending}
        choice = st.selectbox("Select task", list(options.keys()))
        if st.button("Mark complete"):
            pet_n, desc = options[choice]
            if scheduler.complete_task(pet_name=pet_n, description=desc):
                st.success(f"Marked '{desc}' as done!")
                st.rerun()
    else:
        st.success("All tasks complete for the day!")

st.divider()

# ── 4. Daily summary ──────────────────────────────────────────────────────────
st.header("4. Daily Summary")

col_sum, col_reset = st.columns(2)
with col_sum:
    if st.button("Generate summary"):
        st.code(scheduler.summary(), language=None)
with col_reset:
    if st.button("Reset day (recurring tasks only)"):
        scheduler.reset_daily_tasks()
        st.success("Recurring tasks reset for a new day.")
        st.rerun()
