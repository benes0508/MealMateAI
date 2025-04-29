# MealMateAI
Project as part of the course "Workshop on developing scalable AI systems"

# MealMateAI

> MealMateAI is your friendly kitchen companion: it learns your preferences & pantry inventory, then generates personalized meal plans, recipe suggestions, and consolidated shopping lists.  
> It aims to make cooking approachable, reduce food waste, and promote healthier eating habits.

## 📁 Project Structure

```text
MealMateAI/
├── api-gateway/                 # Express.js gateway: auth & routing
├── services/
│   ├── user-service/            # Flask microservice: user auth & pantry CRUD
│   ├── recipe-service/          # Flask microservice: recipe CRUD & search
│   ├── meal-planner-service/    # Flask microservice: weekly menu generation
│   └── notification-service/    # Flask microservice: email reminders
├── frontend/                    # React application (UI)
├── scripts/                     # Helper scripts (e.g. init-db.sh)
├── docker-compose.yml           # Orchestrates all containers
├── .env.example                 # Template for environment variables
└── README.md                    # This file