import axios from 'axios';

const API_URL = '/api'; // Changed from hardcoded Docker service URL

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
  name: string; // Changed from title to match usage in components
  description: string;
  imageUrl?: string;
  prepTime: number;
  cookTime: number;
  servings: number;
  difficulty: 'easy' | 'medium' | 'hard';
  ingredients: string[]; // Simplified to match actual usage
  instructions: string[];
  tags: string[];
  nutritionalInfo: NutritionalInfo;
  dietaryInfo: {
    vegetarian: boolean;
    vegan: boolean;
    glutenFree: boolean;
    dairyFree: boolean;
    nutFree: boolean;
    lowCarb: boolean;
  };
  createdAt: string;
  updatedAt: string;
}

export interface SearchParams {
  query?: string;
  dietary?: string[];
  tags?: string[];
  page?: number;
  limit?: number;
}

const recipeService = {
  async getAllRecipes(filters = {}): Promise<{ recipes: Recipe[]; total: number; page: number; totalPages: number }> {
    try {
      const response = await axios.get(`${API_URL}/recipes`, { params: filters });
      return response.data;
    } catch (error) {
      console.error('Error fetching recipes:', error);
      throw error;
    }
  },

  async getCsvRecipes(): Promise<{ recipes: any[]; total: number }> {
    try {
      const response = await axios.get(`${API_URL}/recipes/csv`);
      return response.data;
    } catch (error) {
      console.error('Error fetching CSV recipes:', error);
      throw error;
    }
  },

  async searchRecipes(params: SearchParams = {}): Promise<{ recipes: Recipe[]; total: number; page: number; total_pages: number }> {
    try {
      const response = await axios.get(`${API_URL}/recipes/search`, { params });
      
      // Clear any cached CSV data since we have database results
      sessionStorage.removeItem('allCsvRecipes');
      sessionStorage.removeItem('filteredCsvRecipes');
      
      // Transform database recipe format to frontend Recipe interface
      const transformedRecipes = response.data.recipes.map((dbRecipe: any) => ({
        id: String(dbRecipe.id),
        name: dbRecipe.name,
        description: dbRecipe.directions || 'No description available',
        imageUrl: dbRecipe.img_src || null,
        prepTime: dbRecipe.prep_time && dbRecipe.prep_time !== 'nan' ? parseInt(dbRecipe.prep_time.split(' ')[0] || '0') || 0 : 0,
        cookTime: dbRecipe.cook_time && dbRecipe.cook_time !== 'nan' ? parseInt(dbRecipe.cook_time.split(' ')[0] || '0') || 0 : 0,
        servings: dbRecipe.servings && dbRecipe.servings !== 'nan' ? parseInt(dbRecipe.servings || '4') || 4 : 4,
        difficulty: dbRecipe.difficulty || 'medium',
        ingredients: dbRecipe.ingredients || [],
        instructions: dbRecipe.directions?.split('\n') || [],
        tags: [...(dbRecipe.tags || []), ...(dbRecipe.cuisine || []), ...(dbRecipe.meal_type || [])],
        nutritionalInfo: {
          calories: 0,
          protein: 0,
          carbs: 0,
          fat: 0
        },
        dietaryInfo: {
          vegetarian: (dbRecipe.dietary_tags || []).includes('vegetarian'),
          vegan: (dbRecipe.dietary_tags || []).includes('vegan'),
          glutenFree: !(dbRecipe.allergens || []).includes('gluten'),
          dairyFree: !(dbRecipe.allergens || []).includes('dairy'),
          nutFree: !(dbRecipe.allergens || []).includes('nuts'),
          lowCarb: (dbRecipe.dietary_tags || []).includes('low-carb')
        },
        createdAt: dbRecipe.created_at,
        updatedAt: dbRecipe.updated_at
      }));

      return {
        recipes: transformedRecipes,
        total: response.data.total,
        page: response.data.page,
        total_pages: response.data.total_pages
      };
    } catch (error) {
      console.error('Error searching recipes:', error);
      throw error;
    }
  },

  async getRecipeById(id: string): Promise<Recipe> {
    try {
      // Check if this is a CSV recipe ID
      if (id.startsWith('csv-')) {
        // Get the recipe from sessionStorage
        const storedRecipe = sessionStorage.getItem('csvRecipeDetails');
        if (storedRecipe) {
          return JSON.parse(storedRecipe);
        } else {
          throw new Error('CSV recipe details not found');
        }
      }

      // Regular database recipe
      const response = await axios.get(`${API_URL}/recipes/${id}`);
      return response.data;
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