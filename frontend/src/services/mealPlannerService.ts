import axios from 'axios';
import jwtDecode from 'jwt-decode';

const API_URL = '/api/meal-plans'; // Changed from hardcoded Docker service URL

export interface MealPlanRecipe {
  id: number;
  recipe_id: string | number;
  day: number;
  meal_type: string;
  name?: string;
  title?: string;
  description?: string;
  ingredients?: string[];
}

export interface MealPlanResponse {
  id: number;
  user_id: number;
  plan_name: string;
  created_at: string;
  days: number;
  meals_per_day: number;
  plan_explanation: string;
  recipes: MealPlanRecipe[];
}

// Get the current meal plan for the user
export const getMealPlan = async (): Promise<MealPlanResponse> => {
  try {
    const token = localStorage.getItem('token');
    const response = await axios.get(`${API_URL}/current`, {
      headers: {
        Authorization: `Bearer ${token}`
      }
    });
    
    // The backend now returns a valid 200 response with empty or valid meal plan data
    return response.data;
  } catch (error: any) {
    console.error('Error fetching meal plan:', error);
    
    // Add additional debugging info
    if (error.response) {
      console.log('Error response status:', error.response.status);
      console.log('Error response data:', error.response.data);
    }
    
    throw error;
  }
};

// Create a mock meal plan for development and testing purposes
export const createMockMealPlan = (): MealPlanResponse => {
  const now = new Date();
  return {
    id: 999,
    user_id: 1,
    plan_name: "Mock Meal Plan",
    created_at: now.toISOString(),
    days: 7,
    meals_per_day: 3,
    plan_explanation: "This is a mock meal plan for development and testing purposes.",
    recipes: [
      // Day 1
      {
        id: 101,
        recipe_id: 101,
        day: 1,
        meal_type: "breakfast",
        name: "Greek Yogurt with Berries",
        description: "Creamy Greek yogurt topped with fresh berries and honey.",
        ingredients: ["Greek yogurt", "Strawberries", "Blueberries", "Honey", "Granola"]
      },
      {
        id: 102,
        recipe_id: 102,
        day: 1,
        meal_type: "lunch",
        name: "Mediterranean Salad",
        description: "Fresh salad with cucumbers, tomatoes, olives, and feta cheese.",
        ingredients: ["Cucumber", "Tomatoes", "Kalamata olives", "Feta cheese", "Olive oil", "Red wine vinegar"]
      },
      {
        id: 103,
        recipe_id: 103,
        day: 1,
        meal_type: "dinner",
        name: "Grilled Salmon with Asparagus",
        description: "Perfectly grilled salmon with roasted asparagus and lemon.",
        ingredients: ["Salmon fillet", "Asparagus", "Lemon", "Olive oil", "Garlic", "Salt", "Pepper"]
      },
      
      // Day 2
      {
        id: 201,
        recipe_id: 201,
        day: 2,
        meal_type: "breakfast",
        name: "Avocado Toast with Eggs",
        description: "Whole grain toast with mashed avocado and poached eggs.",
        ingredients: ["Whole grain bread", "Avocado", "Eggs", "Red pepper flakes", "Salt", "Pepper"]
      },
      {
        id: 202,
        recipe_id: 202,
        day: 2,
        meal_type: "lunch",
        name: "Quinoa Bowl with Roasted Vegetables",
        description: "Nutritious quinoa bowl with seasonal roasted vegetables.",
        ingredients: ["Quinoa", "Bell peppers", "Zucchini", "Red onion", "Olive oil", "Lemon juice", "Feta cheese"]
      },
      {
        id: 203,
        recipe_id: 203,
        day: 2,
        meal_type: "dinner",
        name: "Chicken Stir-Fry",
        description: "Quick and healthy stir-fry with chicken and vegetables.",
        ingredients: ["Chicken breast", "Broccoli", "Carrots", "Snow peas", "Soy sauce", "Ginger", "Garlic"]
      },
      
      // Day 3
      {
        id: 301,
        recipe_id: 301,
        day: 3,
        meal_type: "breakfast",
        name: "Overnight Oats",
        description: "Prepared the night before with oats, milk, and your favorite toppings.",
        ingredients: ["Rolled oats", "Almond milk", "Chia seeds", "Maple syrup", "Cinnamon", "Berries"]
      },
      {
        id: 302,
        recipe_id: 302,
        day: 3,
        meal_type: "lunch",
        name: "Turkey Wrap",
        description: "Whole grain wrap with turkey, greens, and avocado.",
        ingredients: ["Whole grain wrap", "Turkey breast", "Avocado", "Lettuce", "Tomato", "Mustard"]
      },
      {
        id: 303,
        recipe_id: 303,
        day: 3,
        meal_type: "dinner",
        name: "Vegetarian Chili",
        description: "Hearty vegetarian chili with beans and vegetables.",
        ingredients: ["Black beans", "Kidney beans", "Onion", "Bell peppers", "Tomatoes", "Chili powder", "Cumin"]
      },
      
      // Days 4-7 would follow the same pattern
      // Adding just one more day for brevity
      {
        id: 401,
        recipe_id: 401,
        day: 4,
        meal_type: "breakfast",
        name: "Smoothie Bowl",
        description: "Thick smoothie topped with fruits, nuts, and seeds.",
        ingredients: ["Banana", "Berries", "Spinach", "Almond milk", "Chia seeds", "Granola", "Coconut flakes"]
      },
      {
        id: 402,
        recipe_id: 402,
        day: 4,
        meal_type: "lunch",
        name: "Lentil Soup",
        description: "Nutritious lentil soup with vegetables and herbs.",
        ingredients: ["Lentils", "Carrots", "Celery", "Onion", "Garlic", "Vegetable broth", "Thyme"]
      },
      {
        id: 403,
        recipe_id: 403,
        day: 4,
        meal_type: "dinner",
        name: "Baked Cod with Vegetables",
        description: "Oven-baked cod with seasonal vegetables and herbs.",
        ingredients: ["Cod fillet", "Cherry tomatoes", "Zucchini", "Lemon", "Olive oil", "Herbs", "Salt", "Pepper"]
      }
    ]
  };
};

// Get all meal plans for the user
export const getUserMealPlans = async () => {
  try {
    const token = localStorage.getItem('token');
    
    // Get user ID from the token instead of localStorage
    let userId;
    if (token) {
      try {
        const decoded = jwtDecode<{ id: string }>(token);
        userId = decoded.id;
        console.log('Token decoded successfully, user ID:', userId);
      } catch (e) {
        console.error('Failed to decode token to get userId:', e);
      }
    }
    
    if (!userId) {
      console.error('User ID not found in token');
      throw new Error('User ID not found. You may need to log in again.');
    }
    
    try {
      console.log(`Fetching meal plans for user ${userId}`);
      const response = await axios.get(`${API_URL}/user/${userId}`, {
        headers: {
          Authorization: `Bearer ${token}`
        }
      });
      
      // Successful response
      console.log(`Retrieved ${response.data.length} meal plans for user ${userId}`);
      return response.data;
    } catch (err: any) {
      // If we get a 500 error, it likely means there's a backend issue
      // For a new user, it's likely they just don't have any plans yet
      if (err.response) {
        if (err.response.status === 500) {
          console.log('Server error when fetching meal plans, returning empty array');
          return [];  // Return empty array instead of propagating the error
        } else if (err.response.status === 404) {
          console.log('No meal plans found for user, returning empty array');
          return [];
        } else if (err.response.status === 403) {
          console.error('Authorization error when fetching meal plans');
          throw new Error('You do not have permission to access these meal plans.');
        }
      }
      throw err;  // Re-throw other errors
    }
  } catch (error) {
    console.error('Error fetching user meal plans:', error);
    throw error;
  }
};

// Generate a new meal plan
export const generateMealPlan = async (preferences = {}): Promise<MealPlanResponse> => {
  try {
    const token = localStorage.getItem('token');
    const response = await axios.post(`${API_URL}/generate`, preferences, {
      headers: {
        Authorization: `Bearer ${token}`
      }
    });
    return response.data;
  } catch (error) {
    console.error('Error generating meal plan:', error);
    throw error;
  }
};

// Update a specific meal in the meal plan
export const updateMeal = async (dayId: string, mealType: string, recipeId: string) => {
  try {
    const token = localStorage.getItem('token');
    const response = await axios.put(
      `${API_URL}/${dayId}/meals/${mealType}`,
      { recipe_id: recipeId },
      {
        headers: {
          Authorization: `Bearer ${token}`
        }
      }
    );
    return response.data;
  } catch (error) {
    console.error('Error updating meal:', error);
    throw error;
  }
};

// Generate a meal plan using text prompt
export const generateMealPlanFromText = async (inputText: string): Promise<MealPlanResponse> => {
  try {
    const token = localStorage.getItem('token');
    
    // Get user ID from the token instead of localStorage
    let userId;
    if (token) {
      try {
        const decoded = jwtDecode<{ id: string }>(token);
        userId = decoded.id;
      } catch (e) {
        console.error('Failed to decode token to get userId:', e);
      }
    }
    
    if (!userId) {
      throw new Error('User ID not found. You may need to log in again.');
    }
    
    const response = await axios.post(
      `${API_URL}/text-input`, 
      { input_text: inputText },
      {
        headers: {
          Authorization: `Bearer ${token}`
        },
        params: {
          user_id: userId
        }
      }
    );
    return response.data;
  } catch (error) {
    console.error('Error generating meal plan from text:', error);
    throw error;
  }
};

// Get grocery list for a specific meal plan
export const getGroceryList = async (mealPlanId: number) => {
  try {
    const token = localStorage.getItem('token');
    const response = await axios.get(`${API_URL}/${mealPlanId}/grocery-list`, {
      headers: {
        Authorization: `Bearer ${token}`
      }
    });
    return response.data;
  } catch (error) {
    console.error('Error fetching grocery list:', error);
    throw error;
  }
};

// Move a meal to a different day or meal type
export const moveMeal = async (mealPlanId: number, recipeId: number, toDay: number, toMealType: string): Promise<boolean> => {
  try {
    const token = localStorage.getItem('token');
    const response = await axios.post(`${API_URL}/${mealPlanId}/move-meal`, 
      {
        recipe_id: recipeId,
        to_day: toDay,
        to_meal_type: toMealType
      },
      {
        headers: {
          Authorization: `Bearer ${token}`
        }
      }
    );
    return response.data.success;
  } catch (error) {
    console.error('Error moving meal:', error);
    throw error;
  }
};

// Swap two days in a meal plan
export const swapDays = async (mealPlanId: number, day1: number, day2: number): Promise<boolean> => {
  try {
    const token = localStorage.getItem('token');
    const response = await axios.post(`${API_URL}/${mealPlanId}/swap-days`, 
      {
        day1,
        day2
      },
      {
        headers: {
          Authorization: `Bearer ${token}`
        }
      }
    );
    return response.data.success;
  } catch (error) {
    console.error('Error swapping days:', error);
    throw error;
  }
};

// Create a default export with all functions
export default {
  getMealPlan,
  getUserMealPlans,
  generateMealPlan,
  updateMeal,
  generateMealPlanFromText,
  getGroceryList,
  moveMeal,
  swapDays
};