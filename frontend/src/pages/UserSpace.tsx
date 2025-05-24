import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Container,
  Typography,
  Paper,
  Grid,
  Button,
  Tab,
  Tabs,
  Card,
  CardContent,
  CardActions,
  CardMedia,
  Chip,
  Divider,
  CircularProgress,
  Alert
} from '@mui/material';
import {
  CalendarMonth as CalendarIcon,
  Favorite as FavoriteIcon,
  Settings as SettingsIcon,
  Edit as EditIcon,
  RestaurantMenu as RestaurantIcon
} from '@mui/icons-material';
import { useAuth } from '../context/AuthContext';
import authService from '../services/authService';
import mealPlannerService from '../services/mealPlannerService';

// Interface for tab panel props
interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

// Tab panel component
function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`userspace-tabpanel-${index}`}
      aria-labelledby={`userspace-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ p: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

// UserSpace component
const UserSpace = () => {
  const navigate = useNavigate();
  const { user, hasCompletedPreferences } = useAuth();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tabValue, setTabValue] = useState(0);
  const [userProfile, setUserProfile] = useState<any>(null);
  const [savedMealPlans, setSavedMealPlans] = useState<any[]>([]);

  // Handle tab change
  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  // Load user profile and meal plans
  useEffect(() => {
    const fetchUserData = async () => {
      setLoading(true);
      setError(null);
      
      try {
        if (user) {
          // Fetch user profile
          const profileData = await authService.getUserProfile(user.id);
          setUserProfile(profileData);
          
          // Fetch saved meal plans
          const plansData = await mealPlannerService.getUserMealPlans();
          setSavedMealPlans(plansData);
        }
      } catch (err) {
        setError('Failed to load user data. Please try again later.');
        console.error('Error fetching user data:', err);
      } finally {
        setLoading(false);
      }
    };
    
    fetchUserData();
  }, [user]);

  // Navigate to preference setup
  const handleEditPreferences = () => {
    navigate('/preference-setup');
  };

  // Navigate to meal planner
  const handleCreateMealPlan = () => {
    navigate('/meal-planner');
  };

  // Render loading state
  if (loading) {
    return (
      <Container sx={{ py: 5, textAlign: 'center' }}>
        <CircularProgress size={60} />
        <Typography variant="h6" sx={{ mt: 2 }}>
          Loading your personal space...
        </Typography>
      </Container>
    );
  }

  // Render error state
  if (error) {
    return (
      <Container sx={{ py: 5 }}>
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
        <Button variant="contained" onClick={() => window.location.reload()}>
          Retry
        </Button>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ py: 5 }}>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Welcome to Your Space, {user?.name}
        </Typography>
        <Typography variant="subtitle1" color="text.secondary" gutterBottom>
          Manage your meal plans, preferences, and favorite recipes in one place.
        </Typography>
      </Box>

      {/* Preference status banner */}
      {!hasCompletedPreferences && (
        <Alert severity="info" sx={{ mb: 4 }}>
          Complete your preferences to get personalized meal recommendations! 
          <Button 
            color="inherit" 
            size="small" 
            onClick={handleEditPreferences}
            sx={{ ml: 2 }}
          >
            Set Preferences
          </Button>
        </Alert>
      )}

      {/* Action buttons */}
      <Box sx={{ mb: 4, display: 'flex', gap: 2 }}>
        <Button 
          variant="contained" 
          startIcon={<CalendarIcon />}
          onClick={handleCreateMealPlan}
        >
          Create Meal Plan
        </Button>
        <Button 
          variant="outlined" 
          startIcon={<EditIcon />}
          onClick={handleEditPreferences}
        >
          Edit Preferences
        </Button>
      </Box>

      {/* Tabs */}
      <Paper sx={{ mb: 4 }}>
        <Tabs
          value={tabValue}
          onChange={handleTabChange}
          indicatorColor="primary"
          textColor="primary"
          aria-label="user space tabs"
        >
          <Tab icon={<CalendarIcon />} label="My Meal Plans" />
          <Tab icon={<FavoriteIcon />} label="Favorite Recipes" />
          <Tab icon={<SettingsIcon />} label="My Preferences" />
        </Tabs>

        {/* Meal Plans Tab */}
        <TabPanel value={tabValue} index={0}>
          {savedMealPlans.length > 0 ? (
            <Grid container spacing={3}>
              {savedMealPlans.map((plan) => (
                <Grid item key={plan.id} xs={12} sm={6} md={4}>
                  <Card>
                    <CardMedia
                      component="img"
                      height="140"
                      image={plan.image_url || 'https://via.placeholder.com/300x140?text=Meal+Plan'}
                      alt={`Meal Plan for ${plan.created_at}`}
                    />
                    <CardContent>
                      <Typography variant="h6" component="div">
                        {plan.title || `Meal Plan for ${plan.created_at}`}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {new Date(plan.created_at).toLocaleDateString()}
                      </Typography>
                      <Box sx={{ mt: 1 }}>
                        <Chip 
                          size="small" 
                          label={`${plan.meals?.length || 0} meals`} 
                          color="primary" 
                          variant="outlined"
                          sx={{ mr: 1 }}
                        />
                      </Box>
                    </CardContent>
                    <CardActions>
                      <Button size="small" onClick={() => navigate(`/meal-planner/${plan.id}`)}>
                        View Details
                      </Button>
                    </CardActions>
                  </Card>
                </Grid>
              ))}
            </Grid>
          ) : (
            <Box sx={{ textAlign: 'center', py: 4 }}>
              <RestaurantIcon sx={{ fontSize: 60, color: 'text.secondary', mb: 2 }} />
              <Typography variant="h6" gutterBottom>
                No Meal Plans Yet
              </Typography>
              <Typography variant="body2" color="text.secondary" paragraph>
                Start creating personalized meal plans based on your preferences.
              </Typography>
              <Button 
                variant="contained" 
                onClick={handleCreateMealPlan}
              >
                Create Your First Meal Plan
              </Button>
            </Box>
          )}
        </TabPanel>

        {/* Favorite Recipes Tab */}
        <TabPanel value={tabValue} index={1}>
          {userProfile?.favorites?.length > 0 ? (
            <Grid container spacing={3}>
              {userProfile.favorites.map((recipe: any) => (
                <Grid item key={recipe.id} xs={12} sm={6} md={4}>
                  <Card>
                    <CardMedia
                      component="img"
                      height="140"
                      image={recipe.image_url || 'https://via.placeholder.com/300x140?text=Recipe'}
                      alt={recipe.title}
                    />
                    <CardContent>
                      <Typography variant="h6" component="div">
                        {recipe.title}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {recipe.cuisine} • {recipe.preparation_time} mins
                      </Typography>
                    </CardContent>
                    <CardActions>
                      <Button size="small" onClick={() => navigate(`/recipes/${recipe.id}`)}>
                        View Recipe
                      </Button>
                    </CardActions>
                  </Card>
                </Grid>
              ))}
            </Grid>
          ) : (
            <Box sx={{ textAlign: 'center', py: 4 }}>
              <FavoriteIcon sx={{ fontSize: 60, color: 'text.secondary', mb: 2 }} />
              <Typography variant="h6" gutterBottom>
                No Favorite Recipes Yet
              </Typography>
              <Typography variant="body2" color="text.secondary" paragraph>
                Mark recipes as favorites to find them quickly later.
              </Typography>
              <Button 
                variant="contained"
                onClick={() => navigate('/recipes')}
              >
                Explore Recipes
              </Button>
            </Box>
          )}
        </TabPanel>

        {/* Preferences Tab */}
        <TabPanel value={tabValue} index={2}>
          {userProfile?.preferences ? (
            <Box>
              {/* Dietary Restrictions */}
              <Paper sx={{ p: 3, mb: 3 }}>
                <Typography variant="h6" gutterBottom>
                  Dietary Restrictions
                </Typography>
                <Divider sx={{ mb: 2 }} />
                {userProfile.preferences.preferences?.dietary_restrictions?.length > 0 ? (
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                    {userProfile.preferences.preferences.dietary_restrictions.map((restriction: string) => (
                      <Chip key={restriction} label={restriction} />
                    ))}
                  </Box>
                ) : (
                  <Typography variant="body2" color="text.secondary">
                    No dietary restrictions specified.
                  </Typography>
                )}
              </Paper>

              {/* Allergies and Dislikes */}
              <Paper sx={{ p: 3, mb: 3 }}>
                <Typography variant="h6" gutterBottom>
                  Allergies and Dislikes
                </Typography>
                <Divider sx={{ mb: 2 }} />
                <Grid container spacing={3}>
                  <Grid item xs={12} md={6}>
                    <Typography variant="subtitle1" gutterBottom>
                      Allergies
                    </Typography>
                    {userProfile.preferences.allergies?.length > 0 ? (
                      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                        {userProfile.preferences.allergies.map((allergy: string) => (
                          <Chip key={allergy} label={allergy} color="error" variant="outlined" />
                        ))}
                      </Box>
                    ) : (
                      <Typography variant="body2" color="text.secondary">
                        No allergies specified.
                      </Typography>
                    )}
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <Typography variant="subtitle1" gutterBottom>
                      Disliked Ingredients
                    </Typography>
                    {userProfile.preferences.disliked_ingredients?.length > 0 ? (
                      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                        {userProfile.preferences.disliked_ingredients.map((ingredient: string) => (
                          <Chip key={ingredient} label={ingredient} color="warning" variant="outlined" />
                        ))}
                      </Box>
                    ) : (
                      <Typography variant="body2" color="text.secondary">
                        No disliked ingredients specified.
                      </Typography>
                    )}
                  </Grid>
                </Grid>
              </Paper>

              {/* Cuisine Preferences */}
              <Paper sx={{ p: 3, mb: 3 }}>
                <Typography variant="h6" gutterBottom>
                  Cuisine Preferences
                </Typography>
                <Divider sx={{ mb: 2 }} />
                {userProfile.preferences.preferred_cuisines?.length > 0 ? (
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                    {userProfile.preferences.preferred_cuisines.map((cuisine: string) => (
                      <Chip key={cuisine} label={cuisine} color="success" />
                    ))}
                  </Box>
                ) : (
                  <Typography variant="body2" color="text.secondary">
                    No cuisine preferences specified.
                  </Typography>
                )}
              </Paper>

              <Box sx={{ textAlign: 'right', mt: 3 }}>
                <Button
                  variant="contained"
                  color="primary"
                  startIcon={<EditIcon />}
                  onClick={handleEditPreferences}
                >
                  Edit Preferences
                </Button>
              </Box>
            </Box>
          ) : (
            <Box sx={{ textAlign: 'center', py: 4 }}>
              <SettingsIcon sx={{ fontSize: 60, color: 'text.secondary', mb: 2 }} />
              <Typography variant="h6" gutterBottom>
                No Preferences Set
              </Typography>
              <Typography variant="body2" color="text.secondary" paragraph>
                Set your dietary preferences, allergies and favorite cuisines to get personalized meal plans.
              </Typography>
              <Button 
                variant="contained"
                onClick={handleEditPreferences}
              >
                Set Your Preferences
              </Button>
            </Box>
          )}
        </TabPanel>
      </Paper>
    </Container>
  );
};

export default UserSpace;