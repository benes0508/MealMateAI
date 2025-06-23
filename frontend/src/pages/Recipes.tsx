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
  const [csvLoading, setCsvLoading] = useState(false);
  
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
  
  // Tag filter state
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [availableTags, setAvailableTags] = useState<string[]>([]);
  const [showTagFilters, setShowTagFilters] = useState(false);
  const [tagSearchValue, setTagSearchValue] = useState('');
  const [filteredTags, setFilteredTags] = useState<string[]>([]);

  // State to track the source of current recipes
  const [recipeSource, setRecipeSource] = useState<'database' | 'csv' | null>(null);

  useEffect(() => {
    const fetchRecipes = async () => {
      try {
        setLoading(true);
        setError(null);

        // Convert dietary filters object to array of strings for the API
        const dietaryArray = Object.entries(dietaryFilters)
          .filter(([_, value]) => value)
          .map(([key]) => key);
        
        // Check if we're using CSV recipes from a previous load
        const storedCsvRecipes = sessionStorage.getItem('allCsvRecipes');
        const isUsingCsvData = storedCsvRecipes && !dietaryArray.length && selectedTags.length === 0;

        if (isUsingCsvData) {
          // We already have CSV data, just paginate it client-side
          setRecipeSource('csv');
          const allCsvRecipes = JSON.parse(storedCsvRecipes);
          
          // Collect all unique tags for filter UI
          const tagSet = new Set<string>();
          allCsvRecipes.forEach((recipe: any) => {
            const recipeTags = recipe.cuisine_path?.split('/').filter(Boolean) || [];
            recipeTags.forEach((tag: string) => tagSet.add(tag));
          });
          const sortedTags = Array.from(tagSet).sort();
          setAvailableTags(sortedTags);
          setFilteredTags(sortedTags);
          
          // Filter recipes based on search query and selected tags
          let filteredRecipes = allCsvRecipes;
          
          // Apply search query filter
          if (searchParams.query) {
            const query = searchParams.query.toLowerCase();
            filteredRecipes = filteredRecipes.filter((recipe: any) => 
              recipe.recipe_name?.toLowerCase().includes(query)
            );
          }
          
          // Apply tag filter
          if (selectedTags.length > 0) {
            filteredRecipes = filteredRecipes.filter((recipe: any) => {
              const recipeTags = recipe.cuisine_path?.split('/').filter(Boolean) || [];
              return selectedTags.some(tag => recipeTags.includes(tag));
            });
          }
          
          // Store filtered recipes for pagination
          sessionStorage.setItem('filteredCsvRecipes', JSON.stringify(filteredRecipes));
          
          const limit = 12;
          const offset = (page - 1) * limit;
          const paginatedRecipes = filteredRecipes.slice(offset, offset + limit);
          
          // Transform the CSV data to match Recipe type
          const recipes = paginatedRecipes.map((csvRecipe: any) => {
            return {
              id: csvRecipe.Unnamed_0 || String(Math.random()),
              name: csvRecipe.recipe_name || 'Unnamed Recipe',
              description: csvRecipe.directions?.substring(0, 150) + '...' || '',
              imageUrl: csvRecipe.img_src || '/placeholder-recipe.jpg',
              prepTime: parseInt(csvRecipe.prep_time?.split(' ')[0] || '0') || 0,
              cookTime: parseInt(csvRecipe.cook_time?.split(' ')[0] || '0') || 0,
              servings: parseInt(csvRecipe.servings || '0') || 0,
              difficulty: 'medium' as 'easy' | 'medium' | 'hard',
              ingredients: csvRecipe.ingredients?.split(',') || [],
              instructions: csvRecipe.directions?.split('\n') || [],
              tags: csvRecipe.cuisine_path?.split('/').filter(Boolean) || [],
              nutritionalInfo: {
                calories: 0,
                protein: 0,
                carbs: 0,
                fat: 0
              },
              dietaryInfo: {
                vegetarian: false,
                vegan: false,
                glutenFree: false,
                dairyFree: false,
                nutFree: false,
                lowCarb: false
              },
              createdAt: new Date().toISOString(),
              updatedAt: new Date().toISOString()
            };
          });
          
          setRecipes(recipes);
          setTotalPages(Math.ceil(filteredRecipes.length / limit) || 1);
        } else {
          // Update search params with current page, dietary filters and tags
          const params: SearchParams = {
            ...searchParams,
            page,
            dietary: dietaryArray,
            // Future API update would use tags here
            // tags: selectedTags
          };
          
          const response = await recipeService.searchRecipes(params);
          
          // If we got search results, use them
          if (response.recipes && response.recipes.length > 0) {
            // Clear CSV cache if we're using search results
            sessionStorage.removeItem('allCsvRecipes'); 
            setRecipes(response.recipes);
            setTotalPages(response.total_pages || 1);
            setRecipeSource('database');
            
            // Collect tags from database results
            const tagSet = new Set<string>();
            response.recipes.forEach(recipe => {
              recipe.tags.forEach(tag => tagSet.add(tag));
            });
            const sortedTags = Array.from(tagSet).sort();
            setAvailableTags(sortedTags);
            setFilteredTags(sortedTags);
          } 
          // If no search results and this is the initial load (no search query, dietary filters, or tag filters)
          else if (!searchParams.query && !dietaryArray.length && selectedTags.length === 0) {
            // Load CSV recipes automatically
            await loadCsvRecipes(page);
            setRecipeSource('csv');
          }
          // If there's a search query or tags but no results, try searching the CSV data
          else if (searchParams.query || selectedTags.length > 0) {
            // If we don't have CSV data already, load it first
            if (!storedCsvRecipes) {
              const loaded = await loadCsvRecipes();
              if (!loaded) return; // Exit if CSV loading failed
            }
            
            // Now search and filter the CSV data
            const allCsvRecipes = JSON.parse(sessionStorage.getItem('allCsvRecipes') || '[]');
            let filteredRecipes = allCsvRecipes;
            
            // Apply search query filter
            if (searchParams.query) {
              const query = searchParams.query.toLowerCase();
              filteredRecipes = filteredRecipes.filter((recipe: any) => 
                recipe.recipe_name?.toLowerCase().includes(query)
              );
            }
            
            // Apply tag filter
            if (selectedTags.length > 0) {
              filteredRecipes = filteredRecipes.filter((recipe: any) => {
                const recipeTags = recipe.cuisine_path?.split('/').filter(Boolean) || [];
                return selectedTags.some(tag => recipeTags.includes(tag));
              });
            }
            
            // Store filtered recipes for pagination
            sessionStorage.setItem('filteredCsvRecipes', JSON.stringify(filteredRecipes));
            
            const limit = 12;
            const offset = (page - 1) * limit;
            const paginatedRecipes = filteredRecipes.slice(offset, offset + limit);
            
            // Transform the CSV data to match Recipe type
            const recipes = paginatedRecipes.map((csvRecipe: any) => {
              return {
                id: csvRecipe.Unnamed_0 || String(Math.random()),
                name: csvRecipe.recipe_name || 'Unnamed Recipe',
                description: csvRecipe.directions?.substring(0, 150) + '...' || '',
                imageUrl: csvRecipe.img_src || '/placeholder-recipe.jpg',
                prepTime: parseInt(csvRecipe.prep_time?.split(' ')[0] || '0') || 0,
                cookTime: parseInt(csvRecipe.cook_time?.split(' ')[0] || '0') || 0,
                servings: parseInt(csvRecipe.servings || '0') || 0,
                difficulty: 'medium' as 'easy' | 'medium' | 'hard',
                ingredients: csvRecipe.ingredients?.split(',') || [],
                instructions: csvRecipe.directions?.split('\n') || [],
                tags: csvRecipe.cuisine_path?.split('/').filter(Boolean) || [],
                nutritionalInfo: {
                  calories: 0,
                  protein: 0,
                  carbs: 0,
                  fat: 0
                },
                dietaryInfo: {
                  vegetarian: false,
                  vegan: false,
                  glutenFree: false,
                  dairyFree: false,
                  nutFree: false,
                  lowCarb: false
                },
                createdAt: new Date().toISOString(),
                updatedAt: new Date().toISOString()
              };
            });
            
            setRecipes(recipes);
            setTotalPages(Math.ceil(filteredRecipes.length / limit) || 1);
            setRecipeSource('csv');
          }
          // Otherwise, just set empty recipes
          else {
            sessionStorage.removeItem('allCsvRecipes');
            setRecipes([]);
            setTotalPages(1);
          }
        }
      } catch (err) {
        console.error('Failed to fetch recipes:', err);
        setError('Failed to load recipes. Please try again.');
        
        // Try loading CSV recipes as fallback on error
        if (!searchParams.query && selectedTags.length === 0) {
          await loadCsvRecipes(page);
        }
      } finally {
        setLoading(false);
      }
    };

    fetchRecipes();
  }, [page, searchParams.query, dietaryFilters, selectedTags]);

  const handleSearch = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setSearchParams({
      ...searchParams,
      query: (e.currentTarget.elements.namedItem('searchQuery') as HTMLInputElement)?.value || '',
    });
    setPage(1);
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



  const handleTagToggle = (tag: string) => {
    setSelectedTags(prev => {
      if (prev.includes(tag)) {
        return prev.filter(t => t !== tag);
      } else {
        return [...prev, tag];
      }
    });
    setPage(1); // Reset to first page when changing filters
  };
  
  const clearTagFilters = () => {
    setSelectedTags([]);
    setPage(1);
  };

  const handlePageChange = (_event: React.ChangeEvent<unknown>, value: number) => {
    setPage(value);
    window.scrollTo(0, 0);
  };
  
  const viewRecipeDetails = (recipeId: string, recipe?: Recipe) => {
    // If this is a CSV recipe (with a dynamically generated ID)
    if (recipeSource === 'csv' && recipe) {
      // Store the full recipe data in sessionStorage for the details page
      sessionStorage.setItem('csvRecipeDetails', JSON.stringify(recipe));
      navigate(`/recipes/csv-${recipeId}`); // Use a special prefix to indicate it's a CSV recipe
    } else {
      // Regular database recipe
      navigate(`/recipes/${recipeId}`);
    }
  };

  // Define loadCsvRecipes function at the component level to be able to reuse it
  const loadCsvRecipes = async (currentPage = 1) => {
    try {
      setCsvLoading(true);
      setError(null);
      const response = await recipeService.getCsvRecipes();
      
      // Store all CSV recipes in session storage for pagination
      if (response.recipes && response.recipes.length > 0) {
        sessionStorage.setItem('allCsvRecipes', JSON.stringify(response.recipes));
        
        // Collect all unique tags for filter UI
        const tagSet = new Set<string>();
        response.recipes.forEach((recipe: any) => {
          const recipeTags = recipe.cuisine_path?.split('/').filter(Boolean) || [];
          recipeTags.forEach((tag: string) => tagSet.add(tag));
        });
        const sortedTags = Array.from(tagSet).sort();
        setAvailableTags(sortedTags);
        setFilteredTags(sortedTags);
      }
      
      // Check if we need to filter by search query or tags
      let filteredRecipes = response.recipes;
      
      // Apply search query filter
      if (searchParams.query) {
        const query = searchParams.query.toLowerCase();
        filteredRecipes = filteredRecipes.filter((recipe: any) => 
          recipe.recipe_name?.toLowerCase().includes(query)
        );
      }
      
      // Apply tag filter
      if (selectedTags.length > 0) {
        filteredRecipes = filteredRecipes.filter((recipe: any) => {
          const recipeTags = recipe.cuisine_path?.split('/').filter(Boolean) || [];
          return selectedTags.some(tag => recipeTags.includes(tag));
        });
      }
      
      // Store filtered recipes for pagination
      sessionStorage.setItem('filteredCsvRecipes', JSON.stringify(filteredRecipes));
      
      // Calculate pagination
      const limit = 12;
      const offset = (currentPage - 1) * limit;
      const paginatedRecipes = filteredRecipes.slice(offset, offset + limit);
      
      // Transform the CSV data to match Recipe type
      const recipes = paginatedRecipes.map((csvRecipe: any) => {
        return {
          id: csvRecipe.Unnamed_0 || String(Math.random()),
          name: csvRecipe.recipe_name || 'Unnamed Recipe',
          description: csvRecipe.directions?.substring(0, 150) + '...' || '',
          imageUrl: csvRecipe.img_src || '/placeholder-recipe.jpg',
          prepTime: parseInt(csvRecipe.prep_time?.split(' ')[0] || '0') || 0,
          cookTime: parseInt(csvRecipe.cook_time?.split(' ')[0] || '0') || 0,
          servings: parseInt(csvRecipe.servings || '0') || 0,
          difficulty: 'medium' as 'easy' | 'medium' | 'hard',
          ingredients: csvRecipe.ingredients?.split(',') || [],
          instructions: csvRecipe.directions?.split('\n') || [],
          tags: csvRecipe.cuisine_path?.split('/').filter(Boolean) || [],
          nutritionalInfo: {
            calories: 0,
            protein: 0,
            carbs: 0,
            fat: 0
          },
          dietaryInfo: {
            vegetarian: false,
            vegan: false,
            glutenFree: false,
            dairyFree: false,
            nutFree: false,
            lowCarb: false
          },
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString()
        };
      });
      
      setRecipes(recipes);
      setTotalPages(Math.ceil(filteredRecipes.length / limit) || 1);
      setRecipeSource('csv');
      return true;
    } catch (err) {
      console.error('Failed to load CSV recipes:', err);
      setError('Failed to load CSV recipes. Please try again.');
      return false;
    } finally {
      setCsvLoading(false);
    }
  };
  
  // Handler for the button click
  const handleLoadCsvRecipes = () => {
    loadCsvRecipes(page);
  };

  // Filter tags based on search input
  useEffect(() => {
    if (tagSearchValue) {
      const filtered = availableTags.filter(tag => 
        tag.toLowerCase().includes(tagSearchValue.toLowerCase())
      );
      setFilteredTags(filtered);
    } else {
      setFilteredTags(availableTags);
    }
  }, [tagSearchValue, availableTags]);

  const handleTagSearch = (event: React.ChangeEvent<HTMLInputElement>) => {
    const searchText = event.target.value;
    setTagSearchValue(searchText);
    
    if (!searchText) {
      // If search is cleared, show all tags
      setFilteredTags(availableTags);
    } else {
      // Filter tags based on search text
      const filtered = availableTags.filter(tag => 
        tag.toLowerCase().includes(searchText.toLowerCase())
      );
      setFilteredTags(filtered);
    }
  };

  return (
    <Container maxWidth="lg">
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Recipes
          {recipeSource && (
            <Chip
              label={`Source: ${recipeSource === 'database' ? 'Database' : 'CSV'}`}
              color={recipeSource === 'database' ? 'primary' : 'secondary'}
              size="small"
              sx={{ ml: 2, verticalAlign: 'middle' }}
            />
          )}
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

            {availableTags.length > 0 && (
              <>
                <Typography variant="h6" gutterBottom sx={{ mt: 3 }}>
                  Recipe Tags
                  {selectedTags.length > 0 && (
                    <Button 
                      size="small" 
                      sx={{ ml: 2 }}
                      onClick={clearTagFilters}
                    >
                      Clear Tags
                    </Button>
                  )}
                </Typography>
                
                {/* Tag search field */}
                <TextField
                  fullWidth
                  placeholder="Search tags or ingredients (e.g., bacon, fish, etc.)"
                  value={tagSearchValue}
                  onChange={handleTagSearch}
                  sx={{ mb: 2 }}
                  variant="outlined"
                  size="small"
                  InputProps={{
                    startAdornment: (
                      <InputAdornment position="start">
                        <SearchIcon fontSize="small" />
                      </InputAdornment>
                    ),
                    endAdornment: tagSearchValue && (
                      <InputAdornment position="end">
                        <IconButton 
                          onClick={() => {
                            setTagSearchValue('');
                            setFilteredTags(availableTags);
                          }} 
                          edge="end"
                          size="small"
                        >
                          <ClearIcon fontSize="small" />
                        </IconButton>
                      </InputAdornment>
                    )
                  }}
                />

                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mt: 1, maxHeight: '200px', overflowY: 'auto' }}>
                  {filteredTags.length > 0 ? (
                    filteredTags.map(tag => (
                    <Chip
                      key={tag}
                      label={tag}
                      clickable
                      color={selectedTags.includes(tag) ? 'primary' : 'default'}
                      onClick={() => handleTagToggle(tag)}
                      sx={{ m: 0.5 }}
                    />
                  ))
                  ) : (
                    <Typography variant="body2" color="text.secondary" sx={{ p: 1 }}>
                      No tags matching "{tagSearchValue}"
                    </Typography>
                  )}
                </Box>
              </>
            )}
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
                    <Button size="small" onClick={() => viewRecipeDetails(recipe.id, recipe)}>View Recipe</Button>
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
          <Typography variant="body1" color="text.secondary" sx={{ mb: 2 }}>
            Try adjusting your search or filters to find recipes.
          </Typography>
          <Button 
            variant="contained" 
            onClick={handleLoadCsvRecipes}
            disabled={csvLoading}
            sx={{ mt: 2 }}
          >
            {csvLoading ? <CircularProgress size={24} color="inherit" /> : 'Load Sample Recipes from CSV'}
          </Button>
        </Box>
      )}
    </Container>
  );
};

export default Recipes;