import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Container,
  Grid,
  Typography,
  Box,
  Divider,
  Chip,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Card,
  Button,
  CircularProgress,
  Alert,
  Paper
} from '@mui/material';
import {
  Timer as TimerIcon,
  Restaurant as RestaurantIcon,
  BarChart as NutritionIcon,
  Check as CheckIcon,
  ArrowBack as ArrowBackIcon
} from '@mui/icons-material';
import recipeService, { Recipe } from '../services/recipeService';
import { useAuth } from '../context/AuthContext';

const RecipeDetail = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();
  const [recipe, setRecipe] = useState<Recipe | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchRecipeDetails = async () => {
      if (!id) return;

      try {
        setLoading(true);
        setError(null);
        
        // Check if this is a CSV recipe (id starts with "csv-")
        if (id.startsWith('csv-')) {
          // Get the recipe from sessionStorage
          const storedRecipe = sessionStorage.getItem('csvRecipeDetails');
          if (storedRecipe) {
            setRecipe(JSON.parse(storedRecipe));
          } else {
            throw new Error('CSV recipe details not found');
          }
        } else {
          // This is a database recipe, fetch from API
          const data = await recipeService.getRecipeById(id);
          setRecipe(data);
        }
      } catch (err) {
        console.error('Failed to fetch recipe details:', err);
        setError('Failed to load recipe details. Please try again.');
      } finally {
        setLoading(false);
      }
    };

    fetchRecipeDetails();
  }, [id]);

  const handleAddToMealPlan = () => {
    if (id?.startsWith('csv-')) {
      // For CSV recipes, store the entire recipe object
      if (recipe) {
        sessionStorage.setItem('selectedRecipeDetails', JSON.stringify(recipe));
      }
    } else {
      // For database recipes, just store the ID
      sessionStorage.setItem('selectedRecipeId', id || '');
    }
    navigate('/meal-planner');
  };

  // Helper function to convert minutes to hours and minutes format
  const formatTime = (minutes: number): string => {
    if (minutes < 60) {
      return `${minutes} minutes`;
    }
    const hours = Math.floor(minutes / 60);
    const mins = minutes % 60;
    return mins > 0 ? `${hours} hr ${mins} min` : `${hours} hr`;
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '60vh' }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error || !recipe) {
    return (
      <Container maxWidth="md" sx={{ py: 4 }}>
        <Alert severity="error" sx={{ mb: 2 }}>
          {error || 'Recipe not found.'}
        </Alert>
        <Button
          startIcon={<ArrowBackIcon />}
          onClick={() => navigate('/recipes')}
        >
          Back to recipes
        </Button>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg">
      <Box sx={{ mb: 2 }}>
        <Button
          startIcon={<ArrowBackIcon />}
          onClick={() => navigate('/recipes')}
          sx={{ mb: 2 }}
        >
          Back to recipes
        </Button>
      </Box>

      <Grid container spacing={4}>
        {/* Recipe main content */}
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: { xs: 2, sm: 3 }, mb: 3 }}>
            {recipe.imageUrl && (
              <Box
                component="img"
                src={recipe.imageUrl}
                alt={recipe.name}
                sx={{
                  width: '100%',
                  maxHeight: 400,
                  objectFit: 'cover',
                  borderRadius: 1,
                  mb: 3
                }}
              />
            )}

            <Typography variant="h4" component="h1" gutterBottom>
              {recipe.name}
            </Typography>

            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 2 }}>
              {recipe.dietaryInfo?.vegetarian && <Chip label="Vegetarian" color="primary" size="small" />}
              {recipe.dietaryInfo?.vegan && <Chip label="Vegan" color="primary" size="small" />}
              {recipe.dietaryInfo?.glutenFree && <Chip label="Gluten-Free" color="primary" size="small" />}
              {recipe.dietaryInfo?.dairyFree && <Chip label="Dairy-Free" color="primary" size="small" />}
              {recipe.dietaryInfo?.nutFree && <Chip label="Nut-Free" color="primary" size="small" />}
              {recipe.dietaryInfo?.lowCarb && <Chip label="Low-Carb" color="primary" size="small" />}
            </Box>

            <Typography variant="body1" paragraph>
              {recipe.description}
            </Typography>

            <Divider sx={{ my: 3 }} />

            <Typography variant="h5" gutterBottom>
              Ingredients
            </Typography>
            <Typography variant="subtitle2" color="text.secondary" gutterBottom>
              Servings: {recipe.servings}
            </Typography>

            <List>
              {recipe.ingredients && recipe.ingredients.length > 0 ? recipe.ingredients.map((ingredient, index) => (
                <ListItem key={index} sx={{ py: 0.5 }}>
                  <ListItemIcon sx={{ minWidth: 36 }}>
                    <CheckIcon color="primary" fontSize="small" />
                  </ListItemIcon>
                  <ListItemText primary={ingredient} />
                </ListItem>
              )) : (
                <ListItem>
                  <ListItemText primary="No ingredients available" />
                </ListItem>
              )}
            </List>

            <Divider sx={{ my: 3 }} />

            <Typography variant="h5" gutterBottom>
              Instructions
            </Typography>

            <List>
              {recipe.instructions && recipe.instructions.length > 0 ? recipe.instructions.map((step, index) => (
                <ListItem key={index} alignItems="flex-start" sx={{ py: 1 }}>
                  <ListItemIcon sx={{ mt: 0.5 }}>
                    <Box
                      sx={{
                        width: 24,
                        height: 24,
                        borderRadius: '50%',
                        bgcolor: 'primary.main',
                        color: 'primary.contrastText',
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        fontWeight: 'bold',
                      }}
                    >
                      {index + 1}
                    </Box>
                  </ListItemIcon>
                  <ListItemText primary={step} />
                </ListItem>
              )) : (
                <ListItem>
                  <ListItemText primary="No instructions available" />
                </ListItem>
              )}
            </List>
          </Paper>
        </Grid>

        {/* Recipe sidebar */}
        <Grid item xs={12} md={4}>
          <Box sx={{ position: { md: 'sticky' }, top: { md: 24 } }}>
            {/* Recipe info card */}
            <Card sx={{ p: 2, mb: 3 }}>
              <Typography variant="h6" gutterBottom>
                Recipe Info
              </Typography>
              <Grid container spacing={2}>
                <Grid item xs={6}>
                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    <TimerIcon color="action" sx={{ mr: 1 }} />
                    <Box>
                      <Typography variant="body2" color="text.secondary">
                        Prep Time
                      </Typography>
                      <Typography variant="body1">
                        {formatTime(recipe.prepTime)}
                      </Typography>
                    </Box>
                  </Box>
                </Grid>
                <Grid item xs={6}>
                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    <TimerIcon color="action" sx={{ mr: 1 }} />
                    <Box>
                      <Typography variant="body2" color="text.secondary">
                        Cook Time
                      </Typography>
                      <Typography variant="body1">
                        {formatTime(recipe.cookTime)}
                      </Typography>
                    </Box>
                  </Box>
                </Grid>
                <Grid item xs={6}>
                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    <RestaurantIcon color="action" sx={{ mr: 1 }} />
                    <Box>
                      <Typography variant="body2" color="text.secondary">
                        Servings
                      </Typography>
                      <Typography variant="body1">
                        {recipe.servings}
                      </Typography>
                    </Box>
                  </Box>
                </Grid>
                <Grid item xs={6}>
                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                    <NutritionIcon color="action" sx={{ mr: 1 }} />
                    <Box>
                      <Typography variant="body2" color="text.secondary">
                        Calories
                      </Typography>
                      <Typography variant="body1">
                        {recipe.nutritionalInfo?.calories || 'N/A'} kcal
                      </Typography>
                    </Box>
                  </Box>
                </Grid>
              </Grid>

              {isAuthenticated && (
                <Button
                  variant="contained"
                  fullWidth
                  sx={{ mt: 3 }}
                  onClick={handleAddToMealPlan}
                >
                  Add to Meal Plan
                </Button>
              )}
            </Card>

            {/* Recipe tags card */}
            {recipe.tags && recipe.tags.length > 0 && (
              <Card sx={{ p: 2, mb: 3 }}>
                <Typography variant="h6" gutterBottom>
                  Tags
                </Typography>
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                  {recipe.tags.map((tag) => (
                    <Chip
                      key={tag}
                      label={tag}
                      size="small"
                      variant="outlined"
                      sx={{ margin: '2px' }}
                    />
                  ))}
                </Box>
              </Card>
            )}
          </Box>
        </Grid>
      </Grid>
    </Container>
  );
};

export default RecipeDetail;