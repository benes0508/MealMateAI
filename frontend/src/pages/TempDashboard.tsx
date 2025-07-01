import { useNavigate } from 'react-router-dom';
import {
  Box,
  Container,
  Typography,
  Grid,
  Card,
  CardContent,
  Button,
  Divider,
  List,
  ListItem,
  ListItemText,
  Paper,
  CircularProgress,
  Alert,
  Chip,
  IconButton,
  Collapse
} from '@mui/material';
import { 
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  ShoppingCart as ShoppingCartIcon,
  RestaurantMenu as RestaurantMenuIcon,
  Delete as DeleteIcon
} from '@mui/icons-material';
import { useAuth } from '../context/AuthContext';
import { useState, useEffect } from 'react';
import { getUserMealPlans, deleteMealPlan, MealPlanResponse } from '../services/mealPlannerService';

const TempDashboard = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  
  // State for meal plans
  const [mealPlans, setMealPlans] = useState<MealPlanResponse[]>([]);
  const [loadingPlans, setLoadingPlans] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedPlan, setExpandedPlan] = useState<number | null>(null);
  
  // Fetch user's meal plans when component mounts
  useEffect(() => {
    const fetchMealPlans = async () => {
      setLoadingPlans(true);
      try {
        console.log('Fetching meal plans for dashboard...');
        const plans = await getUserMealPlans();
        console.log(`Dashboard received ${plans.length} meal plans`);
        
        // Even if the API returns empty array, we can handle it gracefully
        setMealPlans(plans);
        
        // Clear any previous errors if successful
        setError(null);
      } catch (err: any) {
        console.error('Error fetching meal plans:', err);
        
        // Display more specific error messages based on error type
        if (err.response) {
          // The request was made and the server responded with a status code
          // that falls out of the range of 2xx
          if (err.response.status === 403) {
            setError('You don\'t have permission to access meal plans. Please try logging in again.');
          } else if (err.response.status === 401) {
            setError('Your session has expired. Please log in again.');
          } else if (err.response.status === 500) {
            // For 500 errors, we'll assume there might be an issue with the backend
            console.log('Server returned 500, setting empty meal plans');
            setMealPlans([]);
            // More user-friendly error message
            setError('The server encountered an issue retrieving your meal plans. This could be because you haven\'t created any yet. Try creating a new meal plan.');
            console.error('Server error details:', err.response.data);
          } else {
            setError(`Error loading meal plans: ${err.response.data?.message || err.message}`);
          }
        } else if (err.request) {
          // The request was made but no response was received
          setError('Unable to connect to the server. Please check your internet connection and try again.');
        } else {
          // Something happened in setting up the request that triggered an Error
          setError(`Failed to load meal plans: ${err.message}`);
        }
      } finally {
        setLoadingPlans(false);
      }
    };
    
    if (user) {
      fetchMealPlans();
    } else {
      setLoadingPlans(false);
      setError('Please log in to view your meal plans');
    }
  }, [user]);
  
  // Toggle expanded plan
  const handleTogglePlan = (planId: number) => {
    setExpandedPlan(expandedPlan === planId ? null : planId);
  };

  // Delete meal plan
  const handleDeleteMealPlan = async (planId: number) => {
    if (window.confirm('Are you sure you want to delete this meal plan? This action cannot be undone.')) {
      try {
        setLoadingPlans(true);
        await deleteMealPlan(planId);
        
        // Remove the deleted plan from the state
        setMealPlans(prevPlans => prevPlans.filter(plan => plan.id !== planId));
        
        setLoadingPlans(false);
      } catch (error) {
        console.error('Error deleting meal plan:', error);
        setError('Failed to delete meal plan. Please try again.');
        setLoadingPlans(false);
      }
    }
  };

  return (
    <Container maxWidth="lg" sx={{ py: 6 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Welcome back{user?.name ? `, ${user.name}` : ''}!
      </Typography>
      
      {/* Main Features Section */}
      <Typography variant="h5" sx={{ mb: 3, mt: 4 }}>
        Quick Access
      </Typography>
      
      <Grid container spacing={4} sx={{ mb: 6 }}>
        <Grid item xs={12} md={4}>
          <Card sx={{ height: '100%' }}>
            <CardContent sx={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
              <Typography variant="h6" gutterBottom>
                Meal Planner
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 3, flex: 1 }}>
                Create personalized meal plans based on your preferences and dietary requirements.
                View multiple meal plans, detailed information, and generate grocery lists.
              </Typography>
              <Box sx={{ display: 'flex', gap: 2 }}>
                <Button 
                  variant="contained" 
                  color="primary"
                  onClick={() => navigate('/meal-planner')}
                  startIcon={<RestaurantMenuIcon />}
                >
                  Go to Meal Planner
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={4}>
          <Card sx={{ height: '100%' }}>
            <CardContent sx={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
              <Typography variant="h6" gutterBottom>
                Recipe Browser
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 3, flex: 1 }}>
                Browse our extensive collection of recipes and find inspiration for your next meal.
              </Typography>
              <Button 
                variant="contained" 
                color="primary"
                onClick={() => navigate('/recipes')}
              >
                Browse Recipes
              </Button>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} md={4}>
          <Card sx={{ height: '100%' }}>
            <CardContent sx={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
              <Typography variant="h6" gutterBottom>
                User Profile
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 3, flex: 1 }}>
                Update your preferences, dietary restrictions, and account settings.
              </Typography>
              <Button 
                variant="contained" 
                color="primary"
                onClick={() => navigate('/profile')}
              >
                View Profile
              </Button>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
      
      {/* Past Meal Plans Section */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h5">
          Your Meal Plans
        </Typography>
        <Button 
          variant="contained" 
          color="primary"
          size="small"
          onClick={() => navigate('/create-meal-plan')}
          startIcon={<RestaurantMenuIcon />}
        >
          Create New Meal Plan
        </Button>
      </Box>
      
      {error && (
        <Alert 
          severity="error" 
          sx={{ 
            mb: 3, 
            '& .MuiAlert-message': { 
              fontWeight: 'medium' 
            } 
          }}
          action={
            error.includes("session") || error.includes("permission") ? (
              <Button 
                color="inherit" 
                size="small" 
                onClick={() => navigate('/login')}
              >
                Login Again
              </Button>
            ) : error.includes("server") ? (
              <Button 
                color="inherit" 
                size="small" 
                onClick={() => navigate('/create-meal-plan')}
              >
                Create Plan
              </Button>
            ) : null
          }
        >
          {error}
        </Alert>
      )}
      
      {loadingPlans ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
          <CircularProgress />
        </Box>
      ) : mealPlans && mealPlans.length > 0 ? (
        <List sx={{ width: '100%' }}>
          {mealPlans.map((plan) => (
            <Paper 
              key={plan.id} 
              elevation={1} 
              sx={{ mb: 2, overflow: 'hidden' }}
            >
              <ListItem
                secondaryAction={
                  <IconButton 
                    edge="end" 
                    onClick={() => handleTogglePlan(plan.id)}
                    aria-label="expand"
                  >
                    {expandedPlan === plan.id ? <ExpandLessIcon /> : <ExpandMoreIcon />}
                  </IconButton>
                }
              >
                <ListItemText
                  primary={
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Typography variant="subtitle1">
                        {plan.plan_name || `Meal Plan #${plan.id}`}
                      </Typography>
                      <Chip 
                        size="small" 
                        label={`${plan.days} days`} 
                        color="primary" 
                        variant="outlined" 
                      />
                    </Box>
                  }
                  secondary={
                    <Typography variant="body2" color="text.secondary">
                      Created on {new Date(plan.created_at).toLocaleDateString()}
                    </Typography>
                  }
                />
              </ListItem>
              
              <Collapse in={expandedPlan === plan.id} timeout="auto" unmountOnExit>
                <Box sx={{ p: 3, pt: 0 }}>
                  <Divider sx={{ my: 2 }} />
                  
                  {/* Plan description/prompt used for generation */}
                  {plan.plan_explanation && (
                    <Box sx={{ mb: 2 }}>
                      <Typography variant="subtitle2" gutterBottom>
                        Description/Generation Prompt:
                      </Typography>
                      <Typography variant="body2" paragraph sx={{ pl: 2, borderLeft: '2px solid', borderColor: 'primary.main' }}>
                        {plan.plan_explanation}
                      </Typography>
                    </Box>
                  )}
                  
                  {/* Action buttons */}
                  <Box sx={{ display: 'flex', gap: 2, mt: 2 }}>
                    <Button
                      variant="outlined"
                      size="small"
                      startIcon={<RestaurantMenuIcon />}
                      onClick={() => navigate(`/meal-planner?plan=${plan.id}`)}
                    >
                      View Details
                    </Button>
                    <Button
                      variant="outlined"
                      size="small"
                      startIcon={<ShoppingCartIcon />}
                      onClick={() => navigate(`/meal-planner?plan=${plan.id}&groceries=true`)}
                    >
                      Grocery List
                    </Button>
                    <Button
                      variant="outlined"
                      size="small"
                      color="error"
                      startIcon={<DeleteIcon />}
                      onClick={() => handleDeleteMealPlan(plan.id)}
                    >
                      Delete
                    </Button>
                  </Box>
                </Box>
              </Collapse>
            </Paper>
          ))}
        </List>
      ) : (
        <Paper 
          elevation={1} 
          sx={{ 
            p: 4, 
            display: 'flex', 
            flexDirection: 'column', 
            alignItems: 'center',
            justifyContent: 'center',
            gap: 2,
            mb: 3
          }}
        >
          <RestaurantMenuIcon sx={{ fontSize: 60, color: 'primary.main', opacity: 0.7 }} />
          
          <Typography variant="h6" align="center">
            You don't have any meal plans yet
          </Typography>
          
          <Typography variant="body2" color="text.secondary" align="center" paragraph>
            Create your first meal plan to get started. You can generate a meal plan based on your preferences or using a text description.
          </Typography>
          
          <Button 
            color="primary" 
            variant="contained"
            size="large" 
            onClick={() => navigate('/create-meal-plan')}
            startIcon={<RestaurantMenuIcon />}
          >
            Create Your First Meal Plan
          </Button>
        </Paper>
      )}
    </Container>
  );
};

export default TempDashboard;
