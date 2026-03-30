// classDiagram
//     class Owner {
//         +String name
//         +String contact
//         +__repr__() String
//     }

//     class Pet {
//         +String name
//         +String species
//         +Owner owner
//         +KNOWN_SPECIES$ Set
//         +__repr__() String
//     }

//     class Task {
//         +String title
//         +String category
//         +int duration_minutes
//         +String priority
//         +String notes
//         +bool completed
//         +datetime completed_at
//         +CATEGORIES$ Set
//         +PRIORITIES$ Dict
//         +mark_complete() None
//         +priority_value() int
//         +to_dict() dict
//         +__repr__() String
//     }

//     class Scheduler {
//         +Pet pet
//         -List~Task~ _tasks
//         +add_task(task: Task) None
//         +remove_task(title: String) bool
//         +complete_task(title: String) bool
//         +get_schedule() List~Task~
//         +pending_tasks() List~Task~
//         +completed_tasks() List~Task~
//         +summary() String
//     }

//     // Owner "1" <-- "1" Pet : owned by
//     // Pet "1" <-- "1" Scheduler : manages care for
//     // Scheduler "1" --> "many" Task : schedules
