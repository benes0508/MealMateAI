import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:3000/api';

export interface Ingredient {
  name: string;
  quantity: string;
  unit: string;
}

export interface NutritionalInfo {
  calories: number;
  protein: number;
  carbs: number;
  fat: number;
  fiber?: number;
  sugar?: number;
}

export interface Recipe {
  id: string;
  title: string;
  description: string;
  imageUrl?: string;
  prepTime: number;
  cookTime: number;
  servings: number;
  difficulty: 'easy' | 'medium' | 'hard';
  ingredients: Ingredient[];
  instructions: string[];
  tags: string[];
  nutritionalInfo: NutritionalInfo;
  createdAt: string;
  updatedAt: string;
}

export type RecipeFilters = {
  query?: string;
  tags?: string[];
  difficulty?: string;
  maxPrepTime?: number;
  dietaryRestrictions?: string[];
  excludeIngredients?: string[];
  includeIngredients?: string[];
  page?: number;
  limit?: number;
}

const recipeService = {
  async getAllRecipes(filters: RecipeFilters = {}): Promise<{ recipes: Recipe[]; total: number; page: number; totalPages: number }> {
    try {
      const response = await axios.get(`${API_URL}/recipes`, { params: filters });
      return response.data;
    } catch (error) {
      console.error('Error fetching recipes:', error);
      throw error;
    }
  },

  async getRecipeById(id: string): Promise<Recipe> {
    try {
      const response = await axios.get(`${API_URL}/recipes/${id}`);
      return response.data.recipe;
    } catch (error) {
      console.error(`Error fetching recipe with id ${id}:`, error);
      throw error;
    }
  },

  async getSimilarRecipes(id: string, limit: number = 3): Promise<Recipe[]> {
    try {
      const response = await axios.get(`${API_URL}/recipes/${id}/similar`, {
        params: { limit }
      });
      return response.data.recipes;
    } catch (error) {
      console.error(`Error fetching similar recipes for id ${id}:`, error);
      throw error;
    }
  },

  async getFeaturedRecipes(limit: number = 5): Promise<Recipe[]> {
    try {
      const response = await axios.get(`${API_URL}/recipes/featured`, {
        params: { limit }
      });
      return response.data.recipes;
    } catch (error) {
      console.error('Error fetching featured recipes:', error);
      throw error;
    }
  },

  async getRecipesByTags(tags: string[], limit: number = 10): Promise<Recipe[]> {
    try {
      const response = await axios.get(`${API_URL}/recipes/by-tags`, {
        params: { tags: tags.join(','), limit }
      });
      return response.data.recipes;
    } catch (error) {
      console.error(`Error fetching recipes by tags ${tags}:`, error);
      throw error;
    }
  },

  async getPopularTags(limit: number = 10): Promise<{ tag: string; count: number }[]> {
    try {
      const response = await axios.get(`${API_URL}/recipes/tags/popular`, {
        params: { limit }
      });
      return response.data.tags;
    } catch (error) {
      console.error('Error fetching popular tags:', error);
      throw error;
    }
  },

  async rateRecipe(id: string, rating: number, review?: string): Promise<{ avgRating: number; totalRatings: number }> {
    try {
      const response = await axios.post(`${API_URL}/recipes/${id}/ratings`, {
        rating,
        review
      });
      return response.data;
    } catch (error) {
      console.error(`Error rating recipe ${id}:`, error);
      throw error;
    }
  },

  async saveRecipe(id: string): Promise<void> {
    try {
      await axios.post(`${API_URL}/recipes/${id}/save`);
    } catch (error) {
      console.error(`Error saving recipe ${id}:`, error);
      throw error;
    }
  },

  async unsaveRecipe(id: string): Promise<void> {
    try {
      await axios.delete(`${API_URL}/recipes/${id}/save`);
    } catch (error) {
      console.error(`Error unsaving recipe ${id}:`, error);
      throw error;
    }
  },

  async getSavedRecipes(): Promise<Recipe[]> {
    try {
      const response = await axios.get(`${API_URL}/recipes/saved`);
      return response.data.recipes;
    } catch (error) {
      console.error('Error fetching saved recipes:', error);
      throw error;
    }
  },

  async generateRecipe(preferences: any): Promise<Recipe> {
    try {
      const response = await axios.post(`${API_URL}/recipes/generate`, preferences);
      return response.data.recipe;
    } catch (error) {
      console.error('Error generating recipe:', error);
      throw error;
    }
  }
};

export default recipeService;