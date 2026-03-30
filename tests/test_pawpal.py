from pawpal_system import Task, Pet


def test_mark_complete_changes_status():
    """Task.mark_complete() should flip completed to True."""
    task = Task(description="Morning walk", time="07:30", frequency="daily", priority="high")
    assert task.completed is False

    task.mark_complete()

    assert task.completed is True
    assert task.completed_at is not None


def test_add_task_increases_pet_task_count():
    """Pet.add_task() should increase the pet's task list by one."""
    pet = Pet(name="Mochi", species="cat", age=3)
    assert len(pet.tasks) == 0

    pet.add_task(Task(description="Refill water bowl", time="07:00", frequency="daily", priority="high"))

    assert len(pet.tasks) == 1
