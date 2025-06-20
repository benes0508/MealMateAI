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