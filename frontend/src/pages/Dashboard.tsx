import { useState, useEffect } from 'react';
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
  Alert
} from '@mui/material';
import { CalendarMonth as CalendarIcon, RestaurantMenu as RecipeIcon } from '@mui/icons-material';
import { useAuth } from '../context/AuthContext';
import { getMealPlan } from '../services/mealPlannerService';

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

const Dashboard = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [mealPlans, setMealPlans] = useState<MealPlan[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
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
              dayMeals[mealType] = {
                id: recipe.recipe_id || recipe.id || `recipe-${Math.random()}`,
                name: recipe.name || recipe.title || 'Untitled Meal',
                description: recipe.description || '',
                ingredients: Array.isArray(recipe.ingredients) ? recipe.ingredients : []
              };
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
  }, []);
                recipeId: day.meals.dinner.id,
                name: day.meals.dinner.name
              });
            }
            return meals;
          })
        }];
        
        setMealPlans(transformedData);
      } catch (err) {
        console.error('Failed to fetch meal plans:', err);
        setError('Failed to load your meal plans. Please try again later.');
      } finally {
        setLoading(false);
      }
    };
    
    fetchMealPlans();
  }, [user]);

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
          
          {loading ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', my: 4 }}>
              <CircularProgress />
            </Box>
          ) : mealPlans.length > 0 ? (
            <Grid container spacing={3}>
              {mealPlans.map((plan) => (
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
            <List>
              <ListItem button onClick={() => navigate('/recipes/1')}>
                <ListItemText 
                  primary="Vegetarian Buddha Bowl" 
                  secondary="A healthy mix of grains, vegetables, and proteins"
                />
              </ListItem>
              <Divider />
              <ListItem button onClick={() => navigate('/recipes/2')}>
                <ListItemText 
                  primary="One-Pot Pasta" 
                  secondary="Ready in 20 minutes with minimal cleanup"
                />
              </ListItem>
              <Divider />
              <ListItem button onClick={() => navigate('/recipes/3')}>
                <ListItemText 
                  primary="Classic Chicken Soup" 
                  secondary="Comfort food perfect for cold days"
                />
              </ListItem>
              <Divider />
              <ListItem button onClick={() => navigate('/recipes/4')}>
                <ListItemText 
                  primary="Baked Salmon" 
                  secondary="Rich in omega-3 fatty acids and protein"
                />
              </ListItem>
            </List>
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