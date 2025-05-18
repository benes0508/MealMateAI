import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Container,
  Typography,
  Grid,
  Card,
  CardContent,
  CardMedia,
  CardActions,
  Button,
  Box,
  TextField,
  InputAdornment,
  IconButton,
  Chip,
  FormGroup,
  FormControlLabel,
  Checkbox,
  Pagination,
  CircularProgress,
  Alert,
  Divider
} from '@mui/material';
import {
  Search as SearchIcon,
  Clear as ClearIcon,
  Timer as TimerIcon,
  LocalDining as DiningIcon,
  RestaurantMenu as MenuIcon
} from '@mui/icons-material';
import recipeService, { Recipe, SearchParams } from '../services/recipeService';

// Helper function to convert minutes to hours and minutes format
const formatCookTime = (minutes: number): string => {
  if (minutes < 60) {
    return `${minutes} min`;
  }
  const hours = Math.floor(minutes / 60);
  const mins = minutes % 60;
  return mins > 0 ? `${hours}h ${mins}m` : `${hours}h`;
};

const Recipes = () => {
  const navigate = useNavigate();
  const [recipes, setRecipes] = useState<Recipe[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [searchParams, setSearchParams] = useState<SearchParams>({
    query: '',
    dietary: [],
    limit: 12,
    page: 1
  });
  
  // Filter states
  const [showFilters, setShowFilters] = useState(false);
  const [dietaryFilters, setDietaryFilters] = useState({
    vegetarian: false,
    vegan: false,
    glutenFree: false,
    dairyFree: false,
    nutFree: false,
    lowCarb: false
  });

  useEffect(() => {
    const fetchRecipes = async () => {
      try {
        setLoading(true);
        setError(null);

        // Convert dietary filters object to array of strings for the API
        const dietaryArray = Object.entries(dietaryFilters)
          .filter(([_, value]) => value)
          .map(([key]) => key);
        
        // Update search params with current page and filters
        const params: SearchParams = {
          ...searchParams,
          page,
          dietary: dietaryArray
        };
        
        const response = await recipeService.searchRecipes(params);
        setRecipes(response.recipes);
        setTotalPages(response.total_pages || 1);
      } catch (err) {
        console.error('Failed to fetch recipes:', err);
        setError('Failed to load recipes. Please try again.');
      } finally {
        setLoading(false);
      }
    };

    fetchRecipes();
  }, [page, searchParams.query, dietaryFilters]);

  const handleSearch = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setPage(1); // Reset to first page on new search
  };

  const handleSearchChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setSearchParams(prev => ({
      ...prev,
      query: event.target.value
    }));
  };

  const handleClearSearch = () => {
    setSearchParams(prev => ({
      ...prev,
      query: ''
    }));
    setPage(1);
  };

  const handleDietaryChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setDietaryFilters({
      ...dietaryFilters,
      [event.target.name]: event.target.checked
    });
    setPage(1); // Reset to first page on filter change
  };

  const handlePageChange = (event: React.ChangeEvent<unknown>, value: number) => {
    setPage(value);
    window.scrollTo(0, 0);
  };
  
  const viewRecipeDetails = (recipeId: string) => {
    navigate(`/recipes/${recipeId}`);
  };

  return (
    <Container maxWidth="lg">
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Recipes
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Browse our collection of delicious and healthy recipes
        </Typography>
      </Box>

      {/* Search and filter section */}
      <Box sx={{ mb: 4 }}>
        <Box component="form" onSubmit={handleSearch} sx={{ mb: 2 }}>
          <TextField
            fullWidth
            placeholder="Search by recipe name, ingredient, or cuisine..."
            value={searchParams.query}
            onChange={handleSearchChange}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon />
                </InputAdornment>
              ),
              endAdornment: searchParams.query && (
                <InputAdornment position="end">
                  <IconButton onClick={handleClearSearch} edge="end">
                    <ClearIcon />
                  </IconButton>
                </InputAdornment>
              )
            }}
          />
        </Box>

        <Button 
          variant="outlined" 
          onClick={() => setShowFilters(!showFilters)}
          sx={{ mb: 2 }}
        >
          {showFilters ? 'Hide Filters' : 'Show Filters'}
        </Button>

        {showFilters && (
          <Box sx={{ mb: 2, p: 2, border: 1, borderColor: 'divider', borderRadius: 1 }}>
            <Typography variant="h6" gutterBottom>
              Dietary Preferences
            </Typography>
            <FormGroup row>
              <Grid container>
                <Grid item xs={6} sm={4} md={2}>
                  <FormControlLabel
                    control={
                      <Checkbox
                        checked={dietaryFilters.vegetarian}
                        onChange={handleDietaryChange}
                        name="vegetarian"
                      />
                    }
                    label="Vegetarian"
                  />
                </Grid>
                <Grid item xs={6} sm={4} md={2}>
                  <FormControlLabel
                    control={
                      <Checkbox
                        checked={dietaryFilters.vegan}
                        onChange={handleDietaryChange}
                        name="vegan"
                      />
                    }
                    label="Vegan"
                  />
                </Grid>
                <Grid item xs={6} sm={4} md={2}>
                  <FormControlLabel
                    control={
                      <Checkbox
                        checked={dietaryFilters.glutenFree}
                        onChange={handleDietaryChange}
                        name="glutenFree"
                      />
                    }
                    label="Gluten-Free"
                  />
                </Grid>
                <Grid item xs={6} sm={4} md={2}>
                  <FormControlLabel
                    control={
                      <Checkbox
                        checked={dietaryFilters.dairyFree}
                        onChange={handleDietaryChange}
                        name="dairyFree"
                      />
                    }
                    label="Dairy-Free"
                  />
                </Grid>
                <Grid item xs={6} sm={4} md={2}>
                  <FormControlLabel
                    control={
                      <Checkbox
                        checked={dietaryFilters.nutFree}
                        onChange={handleDietaryChange}
                        name="nutFree"
                      />
                    }
                    label="Nut-Free"
                  />
                </Grid>
                <Grid item xs={6} sm={4} md={2}>
                  <FormControlLabel
                    control={
                      <Checkbox
                        checked={dietaryFilters.lowCarb}
                        onChange={handleDietaryChange}
                        name="lowCarb"
                      />
                    }
                    label="Low-Carb"
                  />
                </Grid>
              </Grid>
            </FormGroup>
          </Box>
        )}
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 4 }}>
          {error}
        </Alert>
      )}

      {/* Recipes grid */}
      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', my: 8 }}>
          <CircularProgress />
        </Box>
      ) : recipes.length > 0 ? (
        <>
          <Grid container spacing={3}>
            {recipes.map((recipe) => (
              <Grid item key={recipe.id} xs={12} sm={6} md={4} lg={3}>
                <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
                  {recipe.imageUrl ? (
                    <CardMedia
                      component="img"
                      height="160"
                      image={recipe.imageUrl}
                      alt={recipe.name}
                      sx={{ objectFit: 'cover' }}
                    />
                  ) : (
                    <Box 
                      sx={{ 
                        height: 160, 
                        bgcolor: 'grey.200', 
                        display: 'flex', 
                        alignItems: 'center', 
                        justifyContent: 'center' 
                      }}
                    >
                      <MenuIcon sx={{ fontSize: 60, color: 'grey.400' }} />
                    </Box>
                  )}

                  <CardContent sx={{ flexGrow: 1 }}>
                    <Typography gutterBottom variant="h6" component="h2">
                      {recipe.name}
                    </Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                      {recipe.description.length > 100 
                        ? `${recipe.description.substring(0, 100)}...` 
                        : recipe.description}
                    </Typography>
                    
                    <Box sx={{ mb: 1, display: 'flex', alignItems: 'center' }}>
                      <TimerIcon fontSize="small" sx={{ mr: 0.5, color: 'text.secondary' }} />
                      <Typography variant="body2" color="text.secondary">
                        {formatCookTime(recipe.prepTime + recipe.cookTime)}
                      </Typography>
                      <DiningIcon fontSize="small" sx={{ ml: 1.5, mr: 0.5, color: 'text.secondary' }} />
                      <Typography variant="body2" color="text.secondary">
                        {recipe.servings} servings
                      </Typography>
                    </Box>
                    
                    <Box sx={{ mt: 1, display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                      {recipe.dietaryInfo.vegetarian && <Chip label="Vegetarian" size="small" variant="outlined" />}
                      {recipe.dietaryInfo.vegan && <Chip label="Vegan" size="small" variant="outlined" />}
                      {recipe.dietaryInfo.glutenFree && <Chip label="Gluten-Free" size="small" variant="outlined" />}
                    </Box>
                  </CardContent>
                  
                  <Divider />
                  
                  <CardActions>
                    <Button size="small" onClick={() => viewRecipeDetails(recipe.id)}>View Recipe</Button>
                  </CardActions>
                </Card>
              </Grid>
            ))}
          </Grid>

          {/* Pagination */}
          <Box sx={{ mt: 4, display: 'flex', justifyContent: 'center' }}>
            <Pagination 
              count={totalPages} 
              page={page} 
              onChange={handlePageChange} 
              color="primary" 
            />
          </Box>
        </>
      ) : (
        <Box sx={{ textAlign: 'center', py: 8 }}>
          <Typography variant="h6">No recipes found</Typography>
          <Typography variant="body1" color="text.secondary">
            Try adjusting your search or filters to find recipes.
          </Typography>
        </Box>
      )}
    </Container>
  );
};

export default Recipes;