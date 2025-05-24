import axios from 'axios';

const API_URL = 'http://api-gateway:4000/api/meal-plans';

export interface MealPlanResponse {
  day: string;
  meals: {
    breakfast?: any;
    lunch?: any;
    dinner?: any;
  };
}

// Get the current meal plan for the user
export const getMealPlan = async () => {
  try {
    const token = localStorage.getItem('token');
    const response = await axios.get(`${API_URL}/current`, {
      headers: {
        Authorization: `Bearer ${token}`
      }
    });
    return response.data;
  } catch (error) {
    console.error('Error fetching meal plan:', error);
    throw error;
  }
};

// Get all meal plans for the user
export const getUserMealPlans = async () => {
  try {
    const token = localStorage.getItem('token');
    const response = await axios.get(`${API_URL}/user`, {
      headers: {
        Authorization: `Bearer ${token}`
      }
    });
    return response.data;
  } catch (error) {
    console.error('Error fetching user meal plans:', error);
    throw error;
  }
};

// Generate a new meal plan
export const generateMealPlan = async (preferences = {}) => {
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

// Create a default export with all functions
export default {
  getMealPlan,
  getUserMealPlans,
  generateMealPlan,
  updateMeal
};