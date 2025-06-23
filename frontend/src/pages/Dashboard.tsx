import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Container,
  Typography,
  Grid,
  Card,
  CardContent,
  CardActions,
  Button,
  Divider,
  Chip,
  List,
  ListItem,
  ListItemText,
  CircularProgress,
  Alert,
  TextField,
  InputAdornment,
  IconButton
} from '@mui/material';
import { CalendarMonth as CalendarIcon, RestaurantMenu as RecipeIcon, Search as SearchIcon, Clear as ClearIcon } from '@mui/icons-material';
import { useAuth } from '../context/AuthContext';
import { getMealPlan } from '../services/mealPlannerService';
import recipeService from '../services/recipeService';

// Define interfaces for meal plan data
interface Meal {
  id: string;
  type: string;
  recipeId: string;
  name: string;
}

interface MealPlan {
  id: string;
  name: string;
  startDate: string;
  endDate: string;
  meals: Meal[];
}

// Interface for recommended recipes
interface RecommendedRecipe {
  id: string;
  name: string;
  description: string;
  tags?: string[];
}

const Dashboard = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [mealPlans, setMealPlans] = useState<MealPlan[]>([]);
  const [filteredMealPlans, setFilteredMealPlans] = useState<MealPlan[]>([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Recommended recipes state
  const [recommendedRecipes, setRecommendedRecipes] = useState<RecommendedRecipe[]>([]);
  const [filteredRecipes, setFilteredRecipes] = useState<RecommendedRecipe[]>([]);
  const [recipeSearchValue, setRecipeSearchValue] = useState('');
  const [recipeTagsLoading, setRecipeTagsLoading] = useState(false);
  
  // Function to transform API response to our MealPlan format
  const transformMealPlanData = (data: any): MealPlan[] => {
    const plans: MealPlan[] = [];
    
    try {
      // Handle the case where data is an object with recipes array
      if (data && data.recipes && Array.isArray(data.recipes)) {
        // Group recipes by day
        const recipesByDay = new Map<number, { breakfast?: any, lunch?: any, dinner?: any }>();
        
        data.recipes.forEach((recipe: any) => {
          const day = recipe.day;
          if (!recipesByDay.has(day)) {
            recipesByDay.set(day, {});
          }
          
          const dayMeals = recipesByDay.get(day);
          if (dayMeals) {
            const mealType = recipe.meal_type.toLowerCase();
            if (mealType === 'breakfast' || mealType === 'lunch' || mealType === 'dinner') {
              if (mealType === 'breakfast' || mealType === 'lunch' || mealType === 'dinner') {
                dayMeals[mealType as keyof typeof dayMeals] = {
                  id: recipe.recipe_id || recipe.id || `recipe-${Math.random()}`,
                  name: recipe.name || recipe.title || 'Untitled Meal',
                  description: recipe.description || '',
                  ingredients: Array.isArray(recipe.ingredients) ? recipe.ingredients : []
                };
              }
            }
          }
        });
        
        // Create a single meal plan object from grouped recipes
        const allMeals: Meal[] = [];
        
        recipesByDay.forEach((meals, day) => {
          const dayStr = `Day ${day}`;
          
          if (meals.breakfast) {
            allMeals.push({
              id: `${dayStr}-breakfast`,
              type: 'breakfast',
              recipeId: meals.breakfast.id,
              name: meals.breakfast.name
            });
          }
          
          if (meals.lunch) {
            allMeals.push({
              id: `${dayStr}-lunch`,
              type: 'lunch',
              recipeId: meals.lunch.id,
              name: meals.lunch.name
            });
          }
          
          if (meals.dinner) {
            allMeals.push({
              id: `${dayStr}-dinner`,
              type: 'dinner',
              recipeId: meals.dinner.id,
              name: meals.dinner.name
            });
          }
        });
        
        // Add the meal plan to the result
        plans.push({
          id: String(data.id) || '1',
          name: data.plan_name || 'Weekly Meal Plan',
          startDate: new Date().toISOString(),
          endDate: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(),
          meals: allMeals
        });
      } else {
        // Fallback for unexpected data format
        plans.push({
          id: '1',
          name: 'Weekly Meal Plan',
          startDate: new Date().toISOString(),
          endDate: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(),
          meals: []
        });
      }
    } catch (e) {
      console.error('Error transforming meal plan data:', e);
      // Return an empty plan on error
      plans.push({
        id: '1',
        name: 'Weekly Meal Plan',
        startDate: new Date().toISOString(),
        endDate: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(),
        meals: []
      });
    }
    
    return plans;
  };
  
  // Fetch meal plans on component mount
  useEffect(() => {
    const fetchMealPlans = async () => {
      try {
        setLoading(true);
        setError(null);
        
        const response = await getMealPlan();
        console.log("Dashboard - Raw meal plan data:", response);
        
        // Transform the API response to our MealPlan format
        const transformedData = transformMealPlanData(response);
        console.log("Dashboard - Transformed meal plan data:", transformedData);
        
        setMealPlans(transformedData);
      } catch (err) {
        console.error("Failed to fetch meal plans:", err);
        setError('Failed to load your meal plans. Please try again later.');
      } finally {
        setLoading(false);
      }
    };
    
    fetchMealPlans();
  }, [user]);
  
  // Load recommended recipes
  useEffect(() => {
    const loadRecommendedRecipes = () => {
      try {
        setRecipeTagsLoading(true);
        
        // Default recommendations - you can replace with API call or other data source
        const mockRecommendations: RecommendedRecipe[] = [
          {
            id: '1',
            name: 'Vegetarian Buddha Bowl',
            description: 'A healthy mix of grains, vegetables, and proteins',
            tags: ['vegetarian', 'healthy', 'bowl']
          },
          {
            id: '2',
            name: 'One-Pot Pasta',
            description: 'Ready in 20 minutes with minimal cleanup',
            tags: ['pasta', 'quick', 'easy']
          },
          {
            id: '3',
            name: 'Classic Chicken Soup',
            description: 'Comfort food perfect for cold days',
            tags: ['chicken', 'soup', 'comfort food']
          },
          {
            id: '4',
            name: 'Baked Salmon',
            description: 'Rich in omega-3 fatty acids and protein',
            tags: ['fish', 'salmon', 'protein']
          },
          {
            id: '5',
            name: 'Bacon & Egg Breakfast Sandwich',
            description: 'Hearty breakfast sandwich with bacon and eggs',
            tags: ['breakfast', 'bacon', 'eggs', 'sandwich']
          },
          {
            id: '6',
            name: 'Bacon Wrapped Chicken',
            description: 'Juicy chicken wrapped in crispy bacon',
            tags: ['bacon', 'chicken', 'dinner']
          }
        ];
        
        setRecommendedRecipes(mockRecommendations);
        setFilteredRecipes(mockRecommendations);
      } catch (error) {
        console.error('Error loading recommended recipes:', error);
      } finally {
        setRecipeTagsLoading(false);
      }
    };
    
    loadRecommendedRecipes();
  }, []);
  
  // Filter recipes based on search input
  // Filter recipes based on search input
  useEffect(() => {
    if (recipeSearchValue.trim() === '') {
      // Show all recipes when search is empty
      setFilteredRecipes(recommendedRecipes);
      return;
    }
    
    const searchTerm = recipeSearchValue.toLowerCase();
    const filtered = recommendedRecipes.filter(recipe => {
      const nameMatch = recipe.name.toLowerCase().includes(searchTerm);
      const tagMatch = recipe.tags?.some(tag => tag.toLowerCase().includes(searchTerm)) || false;
      return nameMatch || tagMatch;
    });
    
    setFilteredRecipes(filtered);
  }, [recipeSearchValue, recommendedRecipes]);
  
  // Filter meal plans based on search term
  useEffect(() => {
    if (searchTerm === '') {
      setFilteredMealPlans(mealPlans);
      return;
    }
    
    const lowercasedFilter = searchTerm.toLowerCase();
    setFilteredMealPlans(
      mealPlans.filter(plan => 
        plan.name.toLowerCase().includes(lowercasedFilter) ||
        plan.meals.some(meal => meal.name.toLowerCase().includes(lowercasedFilter))
      )
    );
  }, [searchTerm, mealPlans]);

  useEffect(() => {
    if (searchTerm === '') {
      setFilteredMealPlans(mealPlans);
    } else {
      const lowercasedFilter = searchTerm.toLowerCase();
      setFilteredMealPlans(
        mealPlans.filter(plan => 
          plan.name.toLowerCase().includes(lowercasedFilter) ||
          plan.meals.some(meal => meal.name.toLowerCase().includes(lowercasedFilter))
        )
      );
    }
  }, [searchTerm, mealPlans]);

  // Fetch recommended recipes (mocked for this example)
  useEffect(() => {
    const fetchRecommendedRecipes = async () => {
      setRecipeTagsLoading(true);
      try {
        // Simulate API call
        const response = await recipeService.getAllRecipes();
        console.log("Recommended recipes data:", response);
        
        // Here you would filter or select recipes based on user preferences, etc.
        setRecommendedRecipes(response);
        setFilteredRecipes(response);
      } catch (err) {
        console.error("Failed to fetch recommended recipes:", err);
      } finally {
        setRecipeTagsLoading(false);
      }
    };
    
    fetchRecommendedRecipes();
  }, []);

  // Filter recipes based on search value
  useEffect(() => {
    if (recipeSearchValue === '') {
      setFilteredRecipes(recommendedRecipes);
    } else {
      const lowercasedFilter = recipeSearchValue.toLowerCase();
      setFilteredRecipes(
        recommendedRecipes.filter(recipe => 
          recipe.name.toLowerCase().includes(lowercasedFilter) ||
          (recipe.description && recipe.description.toLowerCase().includes(lowercasedFilter)) ||
          (recipe.tags && recipe.tags.some(tag => tag.toLowerCase().includes(lowercasedFilter)))
        )
      );
    }
  }, [recipeSearchValue, recommendedRecipes]);

  const handleCreateMealPlan = () => {
    navigate('/meal-planner');
  };

  const handleViewMealPlan = (planId: string) => {
    navigate(`/meal-planner/${planId}`);
  };

  const formatDate = (dateString: string) => {
    const options: Intl.DateTimeFormatOptions = { 
      year: 'numeric', 
      month: 'long', 
      day: 'numeric' 
    };
    return new Date(dateString).toLocaleDateString(undefined, options);
  };

  return (
    <Container maxWidth="lg">
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Welcome back, {user?.name || 'User'}!
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Here's a summary of your meal plans and recommendations.
        </Typography>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <Grid container spacing={4}>
        {/* Active Meal Plans */}
        <Grid item xs={12} md={8}>
          <Box mb={2} display="flex" justifyContent="space-between" alignItems="center">
            <Typography variant="h5" component="h2">
              Your Meal Plans
            </Typography>
            <Button 
              variant="contained" 
              color="primary" 
              startIcon={<CalendarIcon />}
              onClick={handleCreateMealPlan}
            >
              Create New Plan
            </Button>
          </Box>
          
          <TextField
            fullWidth
            variant="outlined"
            placeholder="Search meal plans or recipes..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon color="action" />
                </InputAdornment>
              ),
            }}
            sx={{ mb: 2 }}
          />

          {loading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', my: 4 }}>
              <CircularProgress />
            </Box>
          ) : filteredMealPlans.length > 0 ? (
            <Grid container spacing={3}>
              {filteredMealPlans.map((plan) => (
                <Grid item xs={12} sm={6} key={plan.id}>
                  <Card variant="outlined">
                    <CardContent>
                      <Typography variant="h6" component="h3" gutterBottom>
                        {plan.name}
                      </Typography>
                      <Typography variant="body2" color="text.secondary" gutterBottom>
                        {formatDate(plan.startDate)} - {formatDate(plan.endDate)}
                      </Typography>
                      <Divider sx={{ my: 1 }} />
                      <Typography variant="subtitle2" gutterBottom>
                        Includes:
                      </Typography>
                      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mb: 2 }}>
                        <Chip 
                          label={`${plan.meals.filter(m => m.type === 'breakfast').length} Breakfasts`} 
                          size="small" 
                          color="primary" 
                          variant="outlined" 
                        />
                        <Chip 
                          label={`${plan.meals.filter(m => m.type === 'lunch').length} Lunches`} 
                          size="small" 
                          color="primary" 
                          variant="outlined" 
                        />
                        <Chip 
                          label={`${plan.meals.filter(m => m.type === 'dinner').length} Dinners`} 
                          size="small" 
                          color="primary" 
                          variant="outlined" 
                        />
                      </Box>
                    </CardContent>
                    <CardActions>
                      <Button 
                        size="small" 
                        color="primary"
                        onClick={() => handleViewMealPlan(plan.id)}
                      >
                        View Plan
                      </Button>
                      <Button 
                        size="small"
                        onClick={() => navigate(`/meal-planner/${plan.id}/grocery-list`)}
                      >
                        Grocery List
                      </Button>
                    </CardActions>
                  </Card>
                </Grid>
              ))}
            </Grid>
          ) : (
            <Card variant="outlined" sx={{ p: 3, textAlign: 'center' }}>
              <Typography variant="body1" gutterBottom>
                You don't have any meal plans yet.
              </Typography>
              <Button 
                variant="contained" 
                color="primary" 
                sx={{ mt: 2 }}
                onClick={handleCreateMealPlan}
              >
                Create Your First Plan
              </Button>
            </Card>
          )}
        </Grid>

        {/* Recommendations */}
        <Grid item xs={12} md={4}>
          <Typography variant="h5" component="h2" gutterBottom>
            Recommended Recipes
          </Typography>
          
          <Card variant="outlined">
            <Box sx={{ p: 2, pb: 0 }}>
              <TextField
                fullWidth
                variant="outlined"
                placeholder="Search by name or tag (e.g., bacon, fish)..."
                value={recipeSearchValue}
                onChange={(e) => setRecipeSearchValue(e.target.value)}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <SearchIcon color="action" />
                    </InputAdornment>
                  ),
                  endAdornment: recipeSearchValue && (
                    <InputAdornment position="end">
                      <IconButton 
                        onClick={() => setRecipeSearchValue('')}
                        edge="end"
                        size="small"
                      >
                        <ClearIcon />
                      </IconButton>
                    </InputAdornment>
                  )
                }}
                size="small"
              />
            </Box>

            {recipeTagsLoading ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', my: 4 }}>
                <CircularProgress />
              </Box>
            ) : filteredRecipes.length > 0 ? (
              <List>
                {filteredRecipes.map((recipe, index) => (
                  <React.Fragment key={recipe.id}>
                    <ListItem button onClick={() => navigate(`/recipes/${recipe.id}`)}>
                      <ListItemText 
                        primary={recipe.name} 
                        secondary={
                          <>
                            <Typography variant="body2" component="span">
                              {recipe.description}
                            </Typography>
                            {recipe.tags && recipe.tags.length > 0 && (
                              <Box sx={{ mt: 0.5, display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                                {recipe.tags.map(tag => (
                                  <Chip 
                                    key={tag}
                                    label={tag} 
                                    size="small"
                                    color="primary"
                                    variant="outlined"
                                    onClick={(e) => {
                                      e.stopPropagation(); // Prevent navigating to recipe details
                                      setRecipeSearchValue(tag);
                                    }}
                                    sx={{ height: 20, fontSize: '0.7rem' }}
                                  />
                                ))}
                              </Box>
                            )}
                          </>
                        }
                      />
                    </ListItem>
                    {index < filteredRecipes.length - 1 && <Divider />}
                  </React.Fragment>
                ))}
              </List>
            ) : (
              <Box sx={{ p: 3, textAlign: 'center' }}>
                <Typography variant="body1" gutterBottom>
                  No recipes found matching "{recipeSearchValue}"
                </Typography>
                <Button 
                  variant="outlined" 
                  size="small"
                  onClick={() => setRecipeSearchValue('')}
                >
                  Clear Search
                </Button>
              </Box>
            )}

            <Box sx={{ p: 2 }}>
              <Button 
                fullWidth 
                variant="text"
                startIcon={<RecipeIcon />}
                onClick={() => navigate('/recipes')}
              >
                Browse All Recipes
              </Button>
            </Box>
          </Card>
        </Grid>
      </Grid>
    </Container>
  );
};

export default Dashboard;