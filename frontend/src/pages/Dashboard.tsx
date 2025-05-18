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

// Define a local interface for meal plans that matches the component's expectations
interface MealPlan {
  id: string;
  name: string;
  startDate: string;
  endDate: string;
  meals: {
    id: string;
    type: string;
    recipeId: string;
    name: string;
  }[];
}

const Dashboard = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [mealPlans, setMealPlans] = useState<MealPlan[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  useEffect(() => {
    const fetchMealPlans = async () => {
      try {
        setLoading(true);
        // The getMealPlan function doesn't expect a user ID parameter
        const response = await getMealPlan();
        
        // Transform the response to match the expected MealPlan format
        // This is a temporary solution until backend API is fully implemented
        const transformedData: MealPlan[] = [{
          id: '1',
          name: 'Weekly Meal Plan',
          startDate: new Date().toISOString(),
          endDate: new Date(Date.now() + 7 * 24 * 60 * 60 * 1000).toISOString(),
          meals: response.flatMap((day: { day: string, meals: { breakfast?: any, lunch?: any, dinner?: any }}) => {
            const meals = [];
            if (day.meals.breakfast) {
              meals.push({
                id: `${day.day}-breakfast`,
                type: 'breakfast',
                recipeId: day.meals.breakfast.id,
                name: day.meals.breakfast.name
              });
            }
            if (day.meals.lunch) {
              meals.push({
                id: `${day.day}-lunch`,
                type: 'lunch',
                recipeId: day.meals.lunch.id,
                name: day.meals.lunch.name
              });
            }
            if (day.meals.dinner) {
              meals.push({
                id: `${day.day}-dinner`,
                type: 'dinner',
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