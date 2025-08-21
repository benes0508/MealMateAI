import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { 
  Container, 
  Typography, 
  Box, 
  Grid, 
  Card, 
  CardContent, 
  Button,
  CircularProgress,
  Alert,
  Paper,
  IconButton,
  Tabs,
  Tab,
  Divider,
  List,
  ListItem,
  ListItemText,
  Chip,
  MenuItem,
  Select,
  FormControl,
  InputLabel,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Badge,
  Tooltip,
  Snackbar,
  TextField,
  Collapse,
  ButtonGroup
} from '@mui/material';
import { 
  Close as CloseIcon,
  ShoppingCart as ShoppingCartIcon,
  ExpandMore as ExpandMoreIcon,
  Restaurant as RestaurantIcon,
  Info as InfoIcon,
  DateRange as DateRangeIcon,
  DragIndicator as DragIndicatorIcon,
  SwapVert as SwapVertIcon,
  Undo as UndoIcon,
  Code as CodeIcon,
  SwapHoriz as SwapHorizIcon,
  Search as SearchIcon,
  Add as AddIcon
} from '@mui/icons-material';
import { DragDropContext, Droppable, Draggable, DropResult, DroppableProvided } from 'react-beautiful-dnd';
import { getMealPlan, generateMealPlan, getUserMealPlans, getGroceryList, moveMeal, swapDays, reorderDays, searchRecipeReplacements, searchMultipleCollections, getAvailableCollections, replaceRecipeInMealPlan, Collection } from '../services/mealPlannerService';

interface Meal {
  id: string;
  name: string;
  description: string;
  ingredients: string[];
  image_url?: string;
  meal_type: string;
  recipe_id?: number; // Add recipe_id for API calls
}

interface MealsByType {
  breakfast?: Meal;
  lunch?: Meal;
  dinner?: Meal;
  [key: string]: Meal | undefined;  // Add index signature for dynamic access
}

interface DayPlan {
  day: string;
  dayNumber: number; // Add dayNumber for API calls
  meals: MealsByType;
}

interface GroceryItem {
  name: string;
  quantity: string;
  category: string;
}

interface GroceryList {
  items: GroceryItem[];
}

interface MealPlanMetadata {
  id: number;
  plan_name: string;
  created_at: string;
  days: number;
  meals_per_day: number;
  plan_explanation: string;
}

const MealPlanner: React.FC = () => {
  // Hooks
  const navigate = useNavigate();
  
  // Current meal plan and view state
  const [mealPlan, setMealPlan] = useState<DayPlan[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  
  // Text prompt dialog - REMOVED (functionality moved to chat page)
  
  // Multiple meal plans support
  const [allMealPlans, setAllMealPlans] = useState<MealPlanMetadata[]>([]);
  const [selectedMealPlanId, setSelectedMealPlanId] = useState<number | null>(null);
  const [loadingMealPlans, setLoadingMealPlans] = useState<boolean>(false);
  
  // Grocery list
  const [groceryList, setGroceryList] = useState<GroceryList | null>(null);
  const [loadingGroceryList, setLoadingGroceryList] = useState<boolean>(false);
  const [showGroceryList, setShowGroceryList] = useState<boolean>(false);
  
  // Current meal plan metadata
  const [currentMealPlanMetadata, setCurrentMealPlanMetadata] = useState<MealPlanMetadata | null>(null);
  
  // Drag and drop state management
  const [movingMeal, setMovingMeal] = useState<boolean>(false);
  const [lastMealPlanState, setLastMealPlanState] = useState<DayPlan[] | null>(null);
  const [showUndoSnackbar, setShowUndoSnackbar] = useState<boolean>(false);

  // Recipe replacement state
  const [activeReplaceSearch, setActiveReplaceSearch] = useState<string | null>(null); // "dayNumber-mealType"
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [isSearching, setIsSearching] = useState<boolean>(false);
  
  // Enhanced search state
  const [availableCollections, setAvailableCollections] = useState<Collection[]>([]);
  const [selectedCollections, setSelectedCollections] = useState<string[]>([]);
  const [loadingCollections, setLoadingCollections] = useState<boolean>(false);
  const [searchResultsPage, setSearchResultsPage] = useState<number>(1);
  const [hasMoreResults, setHasMoreResults] = useState<boolean>(false);
  const [maxResultsPerSearch] = useState<number>(20);

  const location = useLocation();

  useEffect(() => {
    // Check if a specific plan was requested via URL parameters
    const queryParams = new URLSearchParams(location.search);
    const planIdParam = queryParams.get('plan');
    const showGroceriesParam = queryParams.get('groceries');
    
    if (planIdParam) {
      // If a specific plan was requested, load it directly
      const planId = parseInt(planIdParam, 10);
      if (!isNaN(planId)) {
        setSelectedMealPlanId(planId);
        fetchMealPlan(planId);
        
        // Show grocery list if requested
        if (showGroceriesParam === 'true') {
          fetchGroceryList(planId);
          setShowGroceryList(true);
        }
      } else {
        // Fallback to loading all plans if planId is invalid
        fetchUserMealPlans();
      }
    } else {
      // Otherwise, load all user meal plans
      fetchUserMealPlans();
    }
  }, [location]);

  useEffect(() => {
    // Only fetch when selectedMealPlanId changes after the initial load
    if (selectedMealPlanId && !location.search.includes(`plan=${selectedMealPlanId}`)) {
      fetchMealPlan(selectedMealPlanId);
    }
  }, [selectedMealPlanId]);

  // Load available collections for recipe search
  useEffect(() => {
    const loadCollections = async () => {
      setLoadingCollections(true);
      try {
        const collections = await getAvailableCollections();
        setAvailableCollections(collections);
      } catch (error) {
        console.error('Failed to load collections:', error);
      } finally {
        setLoadingCollections(false);
      }
    };

    loadCollections();
  }, []);

  // Fetch all meal plans for the current user
  const fetchUserMealPlans = async () => {
    setLoadingMealPlans(true);
    try {
      const data = await getUserMealPlans();
      setAllMealPlans(data);
      
      // Select the most recent meal plan by default
      if (data && data.length > 0) {
        const sortedPlans = [...data].sort((a, b) => 
          new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
        );
        setSelectedMealPlanId(sortedPlans[0].id);
      } else {
        // If no meal plans found, fetch a default one
        fetchMealPlan();
      }
    } catch (err) {
      console.error('Error fetching meal plans:', err);
      // If we can't get the user's meal plans, just load the current one
      fetchMealPlan();
      // Don't show error to user, just silently fall back to current meal plan
    } finally {
      setLoadingMealPlans(false);
    }
  };

  // Fetch grocery list for the current meal plan
  const fetchGroceryList = async (mealPlanId: number, forceRegenerate: boolean = false) => {
    if (!mealPlanId) return;
    
    setLoadingGroceryList(true);
    try {
      const data = await getGroceryList(mealPlanId, forceRegenerate);
      setGroceryList(data);
      // Clear any previous errors
      setError(null);
    } catch (err) {
      console.error('Error fetching grocery list:', err);
      setGroceryList(null);
      // Only show an error alert if we're actively trying to view the grocery list
      if (showGroceryList) {
        setError('Failed to fetch grocery list. Please try again.');
      }
    } finally {
      setLoadingGroceryList(false);
    }
  };

  // Handle meal plan selection
  const handleMealPlanSelect = (planId: number) => {
    setSelectedMealPlanId(planId);
    setShowGroceryList(false); // Reset grocery list view
  };

  // Handle toggle grocery list
  const handleToggleGroceryList = () => {
    if (!showGroceryList && selectedMealPlanId) {
      // Always fetch grocery list when showing (even if cached) to ensure fresh data
      fetchGroceryList(selectedMealPlanId);
    }
    setShowGroceryList(prev => !prev);
  };

  // Transform backend response data into DayPlan[] format
  const transformMealPlanData = (data: any): DayPlan[] => {
    if (!data || !data.recipes || !Array.isArray(data.recipes) || data.recipes.length === 0) {
      console.log('No recipes in meal plan data or empty plan:', data);
      return [];
    }
    
    // Group recipes by day
    const dayMap = new Map<string, any>();
    
    // Process recipes and organize them by day
    data.recipes.forEach((recipe: any) => {
      const dayNumber = recipe.day;
      const day = `Day ${dayNumber}`;
      if (!dayMap.has(day)) {
        dayMap.set(day, {
          day,
          dayNumber,
          meals: {}
        });
      }
      
      const currentDay = dayMap.get(day);
      const mealType = recipe.meal_type.toLowerCase();
      
      // Map to the expected meal structure
      currentDay.meals[mealType] = {
        id: recipe.recipe_id || recipe.id,
        recipe_id: recipe.recipe_id || recipe.id, // Store recipe_id for API calls
        name: recipe.name || recipe.title || 'Untitled Meal',
        description: recipe.description || '',
        ingredients: Array.isArray(recipe.ingredients) ? recipe.ingredients : [],
        meal_type: mealType
      };
    });
    
    // Convert the map to an array and sort by day number to ensure correct order
    return Array.from(dayMap.values()).sort((a, b) => a.dayNumber - b.dayNumber);
  };

  const fetchMealPlan = async (mealPlanId?: number) => {
    setLoading(true);
    setError(null);
    try {
      // If no meal plan ID is provided, fetch the current meal plan
      let data;
      if (mealPlanId) {
        // TODO: Update the mealPlannerService to support fetching a specific meal plan
        // For now, we'll just use the current one
        data = await getMealPlan();
      } else {
        data = await getMealPlan();
      }
      
      console.log("Raw meal plan data:", data); // Debug log
      
      // Check if we have a valid meal plan or an empty one
      if (!data.id) {
        // This is an empty meal plan response (user has no plans yet)
        console.log("No meal plans found for the user. This is normal for new users.");
        setMealPlan([]);
        setCurrentMealPlanMetadata(null);
        return;
      }
      
      // Save the metadata for a valid meal plan
      setCurrentMealPlanMetadata({
        id: data.id,
        plan_name: data.plan_name || 'My Meal Plan',
        created_at: data.created_at,
        days: data.days || 7,
        meals_per_day: data.meals_per_day || 3,
        plan_explanation: data.plan_explanation || ''
      });
      
      const transformedData = transformMealPlanData(data);
      console.log("Transformed meal plan data:", transformedData); // Debug log
      setMealPlan(transformedData);
    } catch (err: any) {
      setError('Failed to load your meal plan. Please try again.');
      console.error("Error fetching meal plan:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateNewPlan = () => {
    navigate('/create-meal-plan');
  };

  // Function to handle undoing the last change
  const handleUndoChange = () => {
    if (lastMealPlanState) {
      setMealPlan(lastMealPlanState);
      setLastMealPlanState(null);
    }
    setShowUndoSnackbar(false);
  };

  const handleCloseUndoSnackbar = () => {
    setShowUndoSnackbar(false);
  };

  // Category detection logic for recipe replacement
  const detectRecipeCategory = (meal: Meal, mealType: string): string => {
    // Map meal types and ingredients to recipe collections
    const mealName = meal.name.toLowerCase();
    const ingredients = Array.isArray(meal.ingredients) ? meal.ingredients.join(' ').toLowerCase() : '';
    
    // Desserts are easy to detect
    if (mealName.includes('cake') || mealName.includes('cookie') || mealName.includes('dessert') || 
        mealName.includes('sweet') || mealName.includes('chocolate') || mealName.includes('ice cream') ||
        ingredients.includes('sugar') && (ingredients.includes('chocolate') || ingredients.includes('vanilla'))) {
      return 'desserts-sweets';
    }
    
    // Breakfast items
    if (mealType === 'breakfast' || mealName.includes('breakfast') || mealName.includes('cereal') ||
        mealName.includes('oats') || mealName.includes('pancake') || mealName.includes('waffle') ||
        mealName.includes('toast') || mealName.includes('yogurt') || mealName.includes('smoothie')) {
      return 'breakfast-morning';
    }
    
    // Protein mains (meat, poultry, seafood)
    if (ingredients.includes('chicken') || ingredients.includes('beef') || ingredients.includes('pork') ||
        ingredients.includes('salmon') || ingredients.includes('fish') || ingredients.includes('shrimp') ||
        ingredients.includes('turkey') || mealName.includes('grilled') || mealName.includes('roasted') ||
        (mealType === 'dinner' && (mealName.includes('chicken') || mealName.includes('beef')))) {
      return 'protein-mains';
    }
    
    // Salads and cold dishes
    if (mealName.includes('salad') || mealName.includes('cold') || mealName.includes('gazpacho') ||
        ingredients.includes('lettuce') || ingredients.includes('greens') || 
        (mealType === 'lunch' && mealName.includes('fresh'))) {
      return 'fresh-cold';
    }
    
    // Quick and light meals
    if (mealType === 'lunch' || mealName.includes('quick') || mealName.includes('light') ||
        mealName.includes('wrap') || mealName.includes('sandwich') || mealName.includes('bowl')) {
      return 'quick-light';
    }
    
    // Comfort food / slow cooked
    if (mealName.includes('stew') || mealName.includes('braised') || mealName.includes('slow') ||
        mealName.includes('comfort') || mealName.includes('casserole') || mealName.includes('soup')) {
      return 'comfort-cooked';
    }
    
    // Vegetarian/vegan
    if (mealName.includes('vegan') || mealName.includes('vegetarian') || 
        (ingredients.includes('tofu') || ingredients.includes('beans') && !ingredients.includes('meat'))) {
      return 'plant-based';
    }
    
    // Baked goods
    if (mealName.includes('bread') || mealName.includes('baked') || mealName.includes('muffin') ||
        ingredients.includes('flour') || ingredients.includes('yeast')) {
      return 'baked-breads';
    }
    
    // Default fallback based on meal type
    if (mealType === 'breakfast') return 'breakfast-morning';
    if (mealType === 'lunch') return 'quick-light';
    if (mealType === 'dinner') return 'protein-mains';
    
    // Ultimate fallback
    return 'quick-light';
  };

  // Get smart collection defaults based on meal type
  const getSmartCollectionDefaults = (mealType: string): string[] => {
    switch (mealType) {
      case 'breakfast':
        return ['breakfast-morning', 'quick-light'];
      case 'lunch':
        return ['quick-light', 'fresh-cold', 'plant-based'];
      case 'dinner':
        return ['protein-mains', 'comfort-cooked'];
      default:
        return ['quick-light', 'protein-mains'];
    }
  };

  // Get color coding for collections
  const getCollectionColor = (collectionName: string): string => {
    const colors = {
      'breakfast-morning': '#FF6B35',  // Orange
      'quick-light': '#4ECDC4',       // Teal
      'protein-mains': '#FF6B9D',     // Pink
      'comfort-cooked': '#A8E6CF',    // Light Green
      'desserts-sweets': '#FFD93D',   // Yellow
      'fresh-cold': '#6BCF7F',        // Green
      'plant-based': '#95E1D3',       // Mint
      'baked-breads': '#C44569'       // Purple
    };
    return colors[collectionName] || '#9E9E9E'; // Default gray
  };

  // Handle starting recipe replacement search
  const handleStartReplaceSearch = (dayNumber: number, mealType: string, currentMeal: Meal) => {
    const searchKey = `${dayNumber}-${mealType}`;
    setActiveReplaceSearch(searchKey);
    setSearchQuery('');
    setSearchResults([]);
    setSearchResultsPage(1);
    setHasMoreResults(false);
    
    // Smart collection selection based on meal type
    const smartCollections = getSmartCollectionDefaults(mealType);
    setSelectedCollections(smartCollections);
    
    // Auto-generate initial search query based on current meal
    const initialQuery = `${mealType} similar to ${currentMeal.name}`;
    setSearchQuery(initialQuery);
    
    // Perform initial search with smart collections
    performEnhancedRecipeSearch(initialQuery, smartCollections);
  };

  // Handle canceling recipe replacement
  const handleCancelReplaceSearch = () => {
    setActiveReplaceSearch(null);
    setSearchQuery('');
    setSearchResults([]);
    setSelectedCollections([]);
    setSearchResultsPage(1);
    setHasMoreResults(false);
    setIsSearching(false);
  };

  // Handle collection selection changes
  const handleCollectionToggle = (collectionName: string) => {
    setSelectedCollections(prev => {
      const newCollections = prev.includes(collectionName)
        ? prev.filter(c => c !== collectionName)
        : [...prev, collectionName];
      
      // Re-search with new collection selection
      if (searchQuery.trim()) {
        performEnhancedRecipeSearch(searchQuery, newCollections);
      }
      
      return newCollections;
    });
  };

  // Handle "Load More" results
  const handleLoadMoreResults = () => {
    if (hasMoreResults && !isSearching) {
      setSearchResultsPage(prev => prev + 1);
      performEnhancedRecipeSearch(searchQuery, selectedCollections, true);
    }
  };

  // Perform recipe search
  const performRecipeSearch = async (query: string, category: string) => {
    if (!query.trim()) {
      setSearchResults([]);
      return;
    }

    setIsSearching(true);
    try {
      const results = await searchRecipeReplacements(query, category, 5);
      setSearchResults(results.results || []);
    } catch (error) {
      console.error('Error searching for recipes:', error);
      setError('Failed to search for recipe replacements. Please try again.');
      setSearchResults([]);
    } finally {
      setIsSearching(false);
    }
  };

  // Enhanced recipe search across multiple collections
  const performEnhancedRecipeSearch = async (query: string, collections: string[], loadMore: boolean = false) => {
    if (!query.trim()) {
      setSearchResults([]);
      return;
    }

    setIsSearching(true);
    try {
      const results = await searchMultipleCollections(query, collections, maxResultsPerSearch);
      
      if (loadMore) {
        // Append to existing results for "Load More" functionality
        setSearchResults(prev => [...prev, ...(results.results || [])]);
      } else {
        // Replace results for new search
        setSearchResults(results.results || []);
      }
      
      // Check if there might be more results (basic heuristic)
      setHasMoreResults((results.results || []).length >= maxResultsPerSearch);
      
    } catch (error) {
      console.error('Error in enhanced recipe search:', error);
      setError('Failed to search for recipe replacements. Please try again.');
      if (!loadMore) {
        setSearchResults([]);
      }
    } finally {
      setIsSearching(false);
    }
  };

  // Handle recipe replacement
  const handleReplaceRecipe = async (dayNumber: number, mealType: string, currentMeal: Meal, newRecipe: any) => {
    if (!selectedMealPlanId || !currentMeal.recipe_id) return;

    setLastMealPlanState([...mealPlan]);
    setIsSearching(true);

    try {
      const success = await replaceRecipeInMealPlan(
        selectedMealPlanId,
        currentMeal.recipe_id,
        newRecipe.recipe_id,
        dayNumber,
        mealType
      );

      if (success) {
        // Update the meal plan optimistically
        const newMealPlan = [...mealPlan];
        const dayIndex = newMealPlan.findIndex(day => day.dayNumber === dayNumber);
        if (dayIndex !== -1) {
          newMealPlan[dayIndex].meals[mealType] = {
            id: newRecipe.recipe_id,
            recipe_id: parseInt(newRecipe.recipe_id),
            name: newRecipe.title,
            description: newRecipe.summary || '',
            ingredients: newRecipe.ingredients_preview || [],
            meal_type: mealType
          };
        }
        setMealPlan(newMealPlan);
        setShowUndoSnackbar(true);
        handleCancelReplaceSearch();
      } else {
        throw new Error('Failed to replace recipe');
      }
    } catch (error) {
      console.error('Error replacing recipe:', error);
      setError('Failed to replace recipe. Please try again.');
      // Revert optimistic update
      if (lastMealPlanState) {
        setMealPlan(lastMealPlanState);
      }
    } finally {
      setIsSearching(false);
    }
  };

  // Function to handle drag and drop of meals and days
  const onDragEnd = async (result: DropResult) => {
    const { source, destination, type } = result;
    
    // If dropped outside the list, do nothing
    if (!destination) {
      return;
    }
    
    // If dropped in the same position, do nothing
    if (source.droppableId === destination.droppableId && source.index === destination.index) {
      return;
    }
    
    // Store the current state for undo functionality
    setLastMealPlanState([...mealPlan]);
    
    setError(null);
    
    // If we're moving a whole day
    if (type === 'days') {
      // Store the original meal plan state for rollback
      const originalMealPlan = [...mealPlan];
      
      // Create the new order by reordering the meal plan array
      const newMealPlan = [...mealPlan];
      const [movedDay] = newMealPlan.splice(source.index, 1);
      newMealPlan.splice(destination.index, 0, movedDay);
      
      // Create the day order array: capture the original day numbers in their new positions
      // BEFORE we update the day numbers
      const dayOrder = newMealPlan.map(dayPlan => dayPlan.dayNumber);
      
      // Update day numbers and titles to match new positions
      newMealPlan.forEach((dayPlan, index) => {
        const newDayNumber = index + 1;
        dayPlan.dayNumber = newDayNumber;
        dayPlan.day = `Day ${newDayNumber}`;
      });
      
      // Update UI optimistically
      setMealPlan(newMealPlan);
      
      // Call API to make the change permanent
      if (selectedMealPlanId) {
        setMovingMeal(true);
        try {
          await reorderDays(selectedMealPlanId, dayOrder);
          // Refresh the meal plan data from server to ensure everything is in sync
          await fetchMealPlan(selectedMealPlanId);
          setShowUndoSnackbar(true);
        } catch (err) {
          console.error('Error reordering days:', err);
          setError('Failed to update meal plan. Please try again.');
          // Revert UI change on error
          setMealPlan(originalMealPlan);
        } finally {
          setMovingMeal(false);
        }
      }
      
      return;
    }
    
    // If we're moving a meal within or between days
    if (type === 'meals') {
      // Parse source and destination IDs
      const sourceDayId = parseInt(source.droppableId.split('-')[1]);
      const sourceMealType = source.droppableId.split('-')[2];
      
      const destDayId = parseInt(destination.droppableId.split('-')[1]);
      const destMealType = destination.droppableId.split('-')[2];
      
      // Find the meal being moved
      const sourceDayIndex = mealPlan.findIndex(day => parseInt(day.day.split(' ')[1]) === sourceDayId);
      if (sourceDayIndex === -1) return;
      
      const sourceMeal = mealPlan[sourceDayIndex].meals[sourceMealType];
      if (!sourceMeal) return;
      
      // Find the destination day
      const destDayIndex = mealPlan.findIndex(day => parseInt(day.day.split(' ')[1]) === destDayId);
      if (destDayIndex === -1) return;
      
      // Get destination meal (if any)
      const destMeal = mealPlan[destDayIndex].meals[destMealType];
      
      // Create a new meal plan with the changes
      const newMealPlan = [...mealPlan];
      
      // Handle same-day swaps differently to avoid overwriting
      if (sourceDayIndex === destDayIndex) {
        // Same day swap - update both meals in a single operation
        newMealPlan[sourceDayIndex] = {
          ...mealPlan[sourceDayIndex],
          meals: {
            ...mealPlan[sourceDayIndex].meals,
            [sourceMealType]: destMeal,
            [destMealType]: sourceMeal
          }
        };
      } else {
        // Different day swap - update each day separately
        newMealPlan[sourceDayIndex] = {
          ...mealPlan[sourceDayIndex],
          meals: {
            ...mealPlan[sourceDayIndex].meals,
            [sourceMealType]: destMeal
          }
        };
        
        newMealPlan[destDayIndex] = {
          ...mealPlan[destDayIndex],
          meals: {
            ...mealPlan[destDayIndex].meals,
            [destMealType]: sourceMeal
          }
        };
      }
      
      // Update UI optimistically
      setMealPlan(newMealPlan);
      
      // Call API to make the change permanent
      if (selectedMealPlanId && sourceMeal.recipe_id) {
        setMovingMeal(true);
        try {
          await moveMeal(
            selectedMealPlanId, 
            sourceMeal.recipe_id, 
            destDayId, 
            destMealType,
            sourceDayId,
            sourceMealType
          );
          setShowUndoSnackbar(true);
        } catch (err) {
          console.error('Error moving meal:', err);
          setError('Failed to update meal plan. Please try again.');
          // Revert UI change on error
          if (lastMealPlanState) {
            setMealPlan(lastMealPlanState);
          } else {
            fetchMealPlan(selectedMealPlanId);
          }
        } finally {
          setMovingMeal(false);
        }
      }
    }
  };

  const renderMealCard = (meal: Meal | undefined, dayNumber: number, mealType: string) => {
    if (!meal) return <Typography color="text.secondary">No meal planned</Typography>;
    
    const handleViewRecipe = () => {
      if (meal.recipe_id) {
        navigate(`/recipes/${meal.recipe_id}`);
      }
    };

    const searchKey = `${dayNumber}-${mealType}`;
    const isActiveSearch = activeReplaceSearch === searchKey;

    const handleSearchQueryChange = (e: React.ChangeEvent<HTMLInputElement>) => {
      const newQuery = e.target.value;
      setSearchQuery(newQuery);
      
      // Debounce search
      clearTimeout((window as any).searchTimeout);
      (window as any).searchTimeout = setTimeout(() => {
        if (selectedCollections.length > 0) {
          performEnhancedRecipeSearch(newQuery, selectedCollections);
        } else {
          // Fallback to single collection search if no collections selected
          const category = detectRecipeCategory(meal, mealType);
          performRecipeSearch(newQuery, category);
        }
      }, 500);
    };
    
    return (
      <Card variant="outlined">
        <CardContent>
          <Typography variant="h6" gutterBottom>{meal.name}</Typography>
          <Typography variant="body2" color="text.secondary" paragraph>
            {meal.description}
          </Typography>
          <Typography variant="subtitle2">Ingredients:</Typography>
          <Box component="ul" sx={{ pl: 2 }}>
            {Array.isArray(meal.ingredients) ? (
              meal.ingredients.map((ingredient, idx) => (
                <Typography component="li" variant="body2" key={idx}>
                  {ingredient}
                </Typography>
              ))
            ) : (
              <Typography component="li" variant="body2">
                No ingredients available
              </Typography>
            )}
          </Box>
          
          {/* Action Buttons */}
          <Box sx={{ mt: 2, display: 'flex', gap: 1, flexWrap: 'wrap' }}>
            {meal.recipe_id && (
              <Button
                size="small"
                variant="outlined"
                onClick={handleViewRecipe}
                startIcon={<RestaurantIcon />}
              >
                View Recipe
              </Button>
            )}
            <Button
              size="small"
              variant="outlined"
              color={isActiveSearch ? "secondary" : "primary"}
              onClick={() => {
                if (isActiveSearch) {
                  handleCancelReplaceSearch();
                } else {
                  handleStartReplaceSearch(dayNumber, mealType, meal);
                }
              }}
              startIcon={isActiveSearch ? <CloseIcon /> : <SwapHorizIcon />}
              disabled={isSearching}
            >
              {isActiveSearch ? 'Cancel' : 'Replace'}
            </Button>
          </Box>

          {/* Inline Search Interface */}
          <Collapse in={isActiveSearch}>
            <Box sx={{ mt: 2, p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
              <Typography variant="subtitle2" gutterBottom>
                Find a replacement for this {mealType}:
              </Typography>
              
              <TextField
                fullWidth
                size="small"
                placeholder="Search for similar recipes..."
                value={searchQuery}
                onChange={handleSearchQueryChange}
                InputProps={{
                  startAdornment: <SearchIcon sx={{ mr: 1, color: 'grey.500' }} />,
                }}
                sx={{ mb: 2 }}
              />

              {/* Collection Selector */}
              <Box sx={{ mb: 2 }}>
                <Typography variant="caption" color="text.secondary" sx={{ mb: 1, display: 'block' }}>
                  Search in collections:
                </Typography>
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, maxHeight: 120, overflowY: 'auto' }}>
                  {availableCollections.map(collection => (
                    <Chip
                      key={collection.name}
                      label={`${collection.description} (${collection.recipe_count})`}
                      size="small"
                      clickable
                      color={selectedCollections.includes(collection.name) ? 'primary' : 'default'}
                      variant={selectedCollections.includes(collection.name) ? 'filled' : 'outlined'}
                      onClick={() => handleCollectionToggle(collection.name)}
                      sx={{ 
                        fontSize: '0.7rem',
                        height: 24,
                        '& .MuiChip-label': { px: 1 }
                      }}
                    />
                  ))}
                  {availableCollections.length === 0 && (
                    <Typography variant="caption" color="text.secondary" sx={{ fontStyle: 'italic' }}>
                      {loadingCollections ? 'Loading collections...' : 'No collections available'}
                    </Typography>
                  )}
                </Box>
                
                {/* Quick Actions */}
                <Box sx={{ mt: 1, display: 'flex', gap: 1 }}>
                  <Button 
                    size="small" 
                    variant="text" 
                    onClick={() => setSelectedCollections(availableCollections.map(c => c.name))}
                    disabled={loadingCollections}
                    sx={{ fontSize: '0.7rem', p: 0.5, minWidth: 'auto' }}
                  >
                    Select All
                  </Button>
                  <Button 
                    size="small" 
                    variant="text" 
                    onClick={() => setSelectedCollections([])}
                    disabled={loadingCollections}
                    sx={{ fontSize: '0.7rem', p: 0.5, minWidth: 'auto' }}
                  >
                    Clear All
                  </Button>
                </Box>
              </Box>

              {/* Search Results */}
              {isSearching ? (
                <Box sx={{ display: 'flex', justifyContent: 'center', py: 2 }}>
                  <CircularProgress size={20} />
                  <Typography variant="body2" sx={{ ml: 1 }}>Searching...</Typography>
                </Box>
              ) : searchResults.length > 0 ? (
                <Box>
                  {/* Results Summary */}
                  <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 1 }}>
                    Found {searchResults.length} recipe{searchResults.length !== 1 ? 's' : ''} 
                    {selectedCollections.length > 0 && (
                      <> in {selectedCollections.length} collection{selectedCollections.length !== 1 ? 's' : ''}</>
                    )}
                  </Typography>
                  
                  {/* Results Container */}
                  <Box sx={{ maxHeight: 400, overflowY: 'auto', mb: 2 }}>
                    {searchResults.map((recipe, idx) => (
                      <Paper 
                        key={recipe.recipe_id} 
                        variant="outlined" 
                        sx={{ 
                          p: 1.5, 
                          mb: 1, 
                          cursor: 'pointer',
                          '&:hover': { bgcolor: 'primary.50' },
                          border: '1px solid',
                          borderColor: 'grey.300'
                        }}
                        onClick={() => handleReplaceRecipe(dayNumber, mealType, meal, recipe)}
                      >
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 1 }}>
                          <Typography variant="subtitle2" sx={{ fontWeight: 600, flex: 1 }}>
                            {recipe.title}
                          </Typography>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, ml: 1 }}>
                            <Chip 
                              label={Math.round(recipe.similarity_score * 100) + '% match'} 
                              size="small" 
                              color="primary"
                              variant="filled"
                              sx={{ fontSize: '0.65rem', height: 20, fontWeight: 600 }}
                            />
                          </Box>
                        </Box>
                        
                        <Typography variant="body2" color="text.secondary" sx={{ 
                          fontSize: '0.75rem', 
                          mb: 1,
                          display: '-webkit-box',
                          WebkitLineClamp: 2,
                          WebkitBoxOrient: 'vertical',
                          overflow: 'hidden'
                        }}>
                          {recipe.summary}
                        </Typography>
                        
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                          <Chip 
                            label={recipe.collection} 
                            size="small" 
                            variant="outlined"
                            sx={{ 
                              fontSize: '0.65rem', 
                              height: 20,
                              bgcolor: getCollectionColor(recipe.collection),
                              color: 'white',
                              border: 'none'
                            }}
                          />
                          {recipe.ingredients_preview && recipe.ingredients_preview.length > 0 && (
                            <Typography variant="caption" color="text.secondary" sx={{ fontSize: '0.65rem' }}>
                              {recipe.ingredients_preview.length} ingredients
                            </Typography>
                          )}
                        </Box>
                      </Paper>
                    ))}
                  </Box>
                  
                  {/* Load More Button */}
                  {hasMoreResults && (
                    <Box sx={{ display: 'flex', justifyContent: 'center', mt: 2 }}>
                      <Button
                        variant="outlined"
                        size="small"
                        onClick={handleLoadMoreResults}
                        disabled={isSearching}
                        startIcon={isSearching ? <CircularProgress size={16} /> : <AddIcon />}
                        sx={{ fontSize: '0.75rem' }}
                      >
                        {isSearching ? 'Loading...' : `Load More Recipes`}
                      </Button>
                    </Box>
                  )}
                </Box>
              ) : searchQuery.trim() && !isSearching ? (
                <Typography variant="body2" color="text.secondary" sx={{ py: 2, textAlign: 'center' }}>
                  No recipes found. Try a different search term.
                </Typography>
              ) : null}
            </Box>
          </Collapse>
        </CardContent>
      </Card>
    );
  };

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Your Meal Plans
        </Typography>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button 
            variant="contained" 
            color="primary"
            onClick={handleGenerateNewPlan}
            disabled={loading}
          >
            Generate New Plan
          </Button>
        </Box>
      </Box>
      
      {/* Meal Plan Selection */}
      {!loadingMealPlans && allMealPlans && allMealPlans.length > 0 && (
        <Box sx={{ mb: 3 }}>
          <FormControl fullWidth variant="outlined" size="small">
            <InputLabel id="meal-plan-select-label">Select Meal Plan</InputLabel>
            <Select
              labelId="meal-plan-select-label"
              id="meal-plan-select"
              value={selectedMealPlanId || ''}
              onChange={(e) => handleMealPlanSelect(Number(e.target.value))}
              label="Select Meal Plan"
            >
              {allMealPlans.map((plan) => (
                <MenuItem key={plan.id} value={plan.id}>
                  {plan.plan_name || `Plan #${plan.id}`} - {new Date(plan.created_at).toLocaleDateString()}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Box>
      )}

      {error && <Alert severity="error" sx={{ mb: 3 }}>{error}</Alert>}
      
      {/* Instructions for modular meal plan */}
      {!showGroceryList && mealPlan.length > 0 && (
        <Alert 
          severity="info" 
          sx={{ mb: 3 }}
          action={
            <IconButton
              aria-label="close"
              color="inherit"
              size="small"
              onClick={() => {
                // Hide instructions in local storage
                localStorage.setItem('mealPlannerInstructionsShown', 'true');
                // Close this alert
                const element = document.querySelector('.meal-plan-instructions');
                if (element) {
                  (element as HTMLElement).style.display = 'none';
                }
              }}
            >
              <CloseIcon fontSize="inherit" />
            </IconButton>
          }
          className="meal-plan-instructions"
          style={{ display: localStorage.getItem('mealPlannerInstructionsShown') === 'true' ? 'none' : 'flex' }}
        >
          <Typography variant="body2">
            <strong>Your meal plan is now modular!</strong> You can:
            <Box component="ul" sx={{ mt: 1, mb: 0 }}>
              <li>Drag and drop meals between different days and meal types</li>
              <li>Reorder entire days by dragging them</li>
              <li>All changes are saved automatically</li>
            </Box>
          </Typography>
        </Alert>
      )}
      
      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
          <CircularProgress />
        </Box>
      ) : mealPlan.length === 0 ? (
        <Box sx={{ textAlign: 'center', py: 4 }}>
          <Paper elevation={2} sx={{ p: 5, maxWidth: 600, mx: 'auto', borderRadius: 2 }}>
            <Box sx={{ mb: 3 }}>
              <RestaurantIcon sx={{ fontSize: 60, color: 'primary.main', mb: 2 }} />
            </Box>
            <Typography variant="h5" gutterBottom fontWeight="bold">
              Welcome to Your Meal Planner!
            </Typography>
            <Typography variant="body1" color="text.secondary" paragraph>
              You haven't created any meal plans yet. Generate your first personalized meal plan to get started with delicious and nutritious meals!
            </Typography>
            <Box sx={{ mt: 4 }}>
              <Button 
                variant="contained" 
                color="primary" 
                size="large"
                onClick={handleGenerateNewPlan}
                sx={{ px: 4, py: 1.5, fontWeight: 'bold' }}
              >
                Generate My First Meal Plan
              </Button>
            </Box>
          </Paper>
        </Box>
      ) : (
        <>
          {/* Meal Plan Metadata */}
          {currentMealPlanMetadata && (
            <Card variant="outlined" sx={{ mb: 3 }}>
              <CardContent>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                  <Typography variant="h6" component="h2">
                    {currentMealPlanMetadata.plan_name || 'My Meal Plan'}
                  </Typography>
                  <Tooltip 
                    title={
                      !selectedMealPlanId ? "Select a meal plan first" :
                      mealPlan.length === 0 ? "No recipes in this meal plan" :
                      loadingGroceryList ? "Generating grocery list..." :
                      showGroceryList ? "Hide the grocery list" : "Generate a grocery list from your meal plan recipes"
                    }
                  >
                    <span>
                      <Button
                        variant="outlined"
                        color="primary"
                        size="small"
                        startIcon={<ShoppingCartIcon />}
                        onClick={handleToggleGroceryList}
                        disabled={!selectedMealPlanId || mealPlan.length === 0 || loadingGroceryList}
                      >
                        {loadingGroceryList ? 'Loading...' : showGroceryList ? 'Hide Grocery List' : 'Show Grocery List'}
                      </Button>
                    </span>
                  </Tooltip>
                </Box>
                <Grid container spacing={2}>
                  <Grid item xs={12} md={6}>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                      <DateRangeIcon fontSize="small" sx={{ mr: 1 }} />
                      <Typography variant="body2" color="text.secondary">
                        Created on: {new Date(currentMealPlanMetadata.created_at).toLocaleDateString()}
                      </Typography>
                    </Box>
                    <Box sx={{ display: 'flex', alignItems: 'center' }}>
                      <InfoIcon fontSize="small" sx={{ mr: 1 }} />
                      <Typography variant="body2" color="text.secondary">
                        {currentMealPlanMetadata.days} days, {currentMealPlanMetadata.meals_per_day} meals per day
                      </Typography>
                    </Box>
                  </Grid>
                  <Grid item xs={12} md={6}>
                    {currentMealPlanMetadata.plan_explanation && (
                      <Typography variant="body2">
                        {currentMealPlanMetadata.plan_explanation}
                      </Typography>
                    )}
                  </Grid>
                </Grid>
              </CardContent>
            </Card>
          )}
          
          {/* Grocery List */}
          {showGroceryList && (
            <Accordion defaultExpanded sx={{ mb: 3 }}>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  <ShoppingCartIcon sx={{ mr: 1 }} />
                  <Typography variant="h6">Grocery List</Typography>
                </Box>
              </AccordionSummary>
              <AccordionDetails>
                {loadingGroceryList ? (
                  <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', py: 4 }}>
                    <CircularProgress size={32} sx={{ mb: 2 }} />
                    <Typography variant="body2" color="text.secondary">
                      Generating your grocery list...
                    </Typography>
                    <Typography variant="caption" color="text.secondary" sx={{ mt: 1 }}>
                      This may take a moment while we analyze your recipes
                    </Typography>
                  </Box>
                ) : error && (error.includes('grocery list') || error.includes('grocery')) ? (
                  <Box sx={{ textAlign: 'center', py: 4 }}>
                    <Alert 
                      severity="warning" 
                      action={
                        <Button 
                          size="small" 
                          onClick={() => {
                            if (selectedMealPlanId) {
                              setError(null);
                              fetchGroceryList(selectedMealPlanId, true); // Force regenerate on retry
                            }
                          }}
                        >
                          Retry
                        </Button>
                      }
                      sx={{ mb: 2 }}
                    >
                      Failed to generate grocery list
                    </Alert>
                    <Typography variant="body2" color="text.secondary">
                      There was an issue generating your grocery list. You can try again or manually review your meal plan recipes.
                    </Typography>
                  </Box>
                ) : groceryList && groceryList.items && groceryList.items.length > 0 ? (
                  <Box>
                    <Box sx={{ mb: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <Typography variant="body2" color="text.secondary">
                        {groceryList.items.length} items organized by category
                      </Typography>
                      <Button
                        size="small"
                        variant="outlined"
                        onClick={() => {
                          if (selectedMealPlanId) {
                            fetchGroceryList(selectedMealPlanId, true); // Force regenerate
                          }
                        }}
                        disabled={loadingGroceryList}
                      >
                        Refresh List
                      </Button>
                    </Box>
                    
                    {/* Group by category */}
                    {Object.entries(
                      groceryList.items.reduce((acc: Record<string, GroceryItem[]>, item) => {
                        const category = item.category || 'Other';
                        if (!acc[category]) acc[category] = [];
                        acc[category].push(item);
                        return acc;
                      }, {} as Record<string, GroceryItem[]>)
                    ).map(([category, items]) => (
                      <Paper key={category} variant="outlined" sx={{ mb: 2, p: 2 }}>
                        <Typography variant="subtitle1" gutterBottom sx={{ 
                          fontWeight: 'bold',
                          color: 'primary.main',
                          borderBottom: '1px solid',
                          borderColor: 'divider',
                          pb: 1
                        }}>
                          {category} ({items.length} items)
                        </Typography>
                        <List dense>
                          {items.map((item, idx) => (
                            <ListItem 
                              key={idx} 
                              divider={idx < items.length - 1}
                              sx={{ 
                                py: 0.5,
                                '&:hover': { bgcolor: 'grey.50' }
                              }}
                            >
                              <ListItemText 
                                primary={
                                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                    <Typography variant="body2" sx={{ fontWeight: 500 }}>
                                      {item.name}
                                    </Typography>
                                    <Chip 
                                      label={item.quantity} 
                                      size="small" 
                                      variant="outlined"
                                      sx={{ fontSize: '0.7rem' }}
                                    />
                                  </Box>
                                }
                              />
                            </ListItem>
                          ))}
                        </List>
                      </Paper>
                    ))}
                    
                    <Typography variant="caption" color="text.secondary" sx={{ mt: 2, display: 'block', textAlign: 'center' }}>
                      💡 Tip: This list combines and organizes ingredients from all recipes in your meal plan
                    </Typography>
                  </Box>
                ) : (
                  <Box sx={{ textAlign: 'center', py: 4 }}>
                    <ShoppingCartIcon sx={{ fontSize: 48, color: 'grey.400', mb: 2 }} />
                    <Typography variant="body1" color="text.secondary" gutterBottom>
                      No grocery list available
                    </Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                      Generate a grocery list from your meal plan recipes
                    </Typography>
                    {selectedMealPlanId && mealPlan.length > 0 && (
                      <Button
                        variant="contained"
                        color="primary"
                        onClick={() => fetchGroceryList(selectedMealPlanId)} // Uses cached if available
                        disabled={loadingGroceryList}
                        startIcon={<ShoppingCartIcon />}
                      >
                        Generate Grocery List
                      </Button>
                    )}
                  </Box>
                )}
              </AccordionDetails>
            </Accordion>
          )}
          
          {/* Meal Plan Days */}
          <DragDropContext onDragEnd={onDragEnd}>
            <Droppable droppableId="days" type="days">
              {(provided: DroppableProvided) => (
                <Box 
                  ref={provided.innerRef}
                  {...provided.droppableProps}
                >
                  {mealPlan.map((dayPlan, idx) => (
                    <Draggable 
                      key={`day-${dayPlan.dayNumber}`} 
                      draggableId={`day-${dayPlan.dayNumber}`} 
                      index={idx}
                    >
                      {(dragProvided) => (
                        <Box 
                          ref={dragProvided.innerRef}
                          {...dragProvided.draggableProps}
                          sx={{ mb: 4 }}
                        >
                          <Paper elevation={1} sx={{ p: 2, mb: 1 }}>
                            <Box sx={{ 
                              display: 'flex', 
                              alignItems: 'center', 
                              justifyContent: 'space-between', 
                              mb: 2 
                            }}>
                              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                                <Box 
                                  {...dragProvided.dragHandleProps} 
                                  sx={{ 
                                    mr: 1, 
                                    cursor: 'grab',
                                    display: 'flex',
                                    alignItems: 'center',
                                    padding: '4px',
                                    borderRadius: '4px',
                                    '&:hover': {
                                      backgroundColor: 'rgba(0, 0, 0, 0.04)'
                                    }
                                  }}
                                  aria-label={`Drag ${dayPlan.day} to reorder`}
                                >
                                  <DragIndicatorIcon color="primary" />
                                </Box>
                                <Typography variant="h5">
                                  {dayPlan.day}
                                </Typography>
                              </Box>
                              <Tooltip title="Drag to reorder days">
                                <SwapVertIcon color="action" fontSize="small" />
                              </Tooltip>
                            </Box>
                            
                            <Grid container spacing={3}>
                              <Grid item xs={12} md={4}>
                                <Typography variant="h6" gutterBottom>Breakfast</Typography>
                                <Droppable 
                                  droppableId={`meal-${dayPlan.dayNumber}-breakfast`} 
                                  type="meals"
                                >
                                  {(breakfastProvided, snapshot) => (
                                    <Box
                                      ref={breakfastProvided.innerRef}
                                      {...breakfastProvided.droppableProps}
                                      sx={{ 
                                        minHeight: '200px', 
                                        backgroundColor: snapshot.isDraggingOver ? 'rgba(25, 118, 210, 0.08)' : 'transparent',
                                        transition: 'all 0.2s ease',
                                        borderRadius: 1,
                                        border: snapshot.isDraggingOver ? '2px dashed #1976d2' : '2px dashed transparent',
                                        padding: 1
                                      }}
                                      aria-label={`Drop zone for breakfast on ${dayPlan.day}`}
                                    >
                                      {dayPlan.meals.breakfast && (
                                        <Draggable 
                                          draggableId={`meal-${dayPlan.dayNumber}-breakfast-${dayPlan.meals.breakfast.id}`}
                                          index={0}
                                        >
                                          {(mealProvided) => (
                                            <div
                                              ref={mealProvided.innerRef}
                                              {...mealProvided.draggableProps}
                                              {...mealProvided.dragHandleProps}
                                              style={{
                                                ...mealProvided.draggableProps.style,
                                                cursor: 'grab'
                                              }}
                                              aria-label={`Drag ${dayPlan.meals.breakfast?.name} to move to another slot`}
                                            >
                                              {renderMealCard(dayPlan.meals.breakfast, dayPlan.dayNumber, 'breakfast')}
                                            </div>
                                          )}
                                        </Draggable>
                                      )}
                                      {!dayPlan.meals.breakfast && (
                                        <Card variant="outlined" sx={{ 
                                          height: '100%', 
                                          minHeight: '100px', 
                                          display: 'flex', 
                                          alignItems: 'center', 
                                          justifyContent: 'center',
                                          borderStyle: 'dashed',
                                          borderWidth: '1px',
                                          backgroundColor: snapshot.isDraggingOver ? 'rgba(25, 118, 210, 0.04)' : 'transparent'
                                        }}>
                                          <Typography color="text.secondary">Drop a meal here</Typography>
                                        </Card>
                                      )}
                                      {breakfastProvided.placeholder}
                                    </Box>
                                  )}
                                </Droppable>
                              </Grid>
                              
                              <Grid item xs={12} md={4}>
                                <Typography variant="h6" gutterBottom>Lunch</Typography>
                                <Droppable 
                                  droppableId={`meal-${dayPlan.dayNumber}-lunch`} 
                                  type="meals"
                                >
                                  {(lunchProvided, snapshot) => (
                                    <Box
                                      ref={lunchProvided.innerRef}
                                      {...lunchProvided.droppableProps}
                                      sx={{ 
                                        minHeight: '200px', 
                                        backgroundColor: snapshot.isDraggingOver ? 'rgba(25, 118, 210, 0.08)' : 'transparent',
                                        transition: 'all 0.2s ease',
                                        borderRadius: 1,
                                        border: snapshot.isDraggingOver ? '2px dashed #1976d2' : '2px dashed transparent',
                                        padding: 1
                                      }}
                                      aria-label={`Drop zone for lunch on ${dayPlan.day}`}
                                    >
                                      {dayPlan.meals.lunch && (
                                        <Draggable 
                                          draggableId={`meal-${dayPlan.dayNumber}-lunch-${dayPlan.meals.lunch.id}`}
                                          index={0}
                                        >
                                          {(mealProvided) => (
                                            <div
                                              ref={mealProvided.innerRef}
                                              {...mealProvided.draggableProps}
                                              {...mealProvided.dragHandleProps}
                                              style={{
                                                ...mealProvided.draggableProps.style,
                                                cursor: 'grab'
                                              }}
                                              aria-label={`Drag ${dayPlan.meals.lunch?.name} to move to another slot`}
                                            >
                                              {renderMealCard(dayPlan.meals.lunch, dayPlan.dayNumber, 'lunch')}
                                            </div>
                                          )}
                                        </Draggable>
                                      )}
                                      {!dayPlan.meals.lunch && (
                                        <Card variant="outlined" sx={{ 
                                          height: '100%', 
                                          minHeight: '100px', 
                                          display: 'flex', 
                                          alignItems: 'center', 
                                          justifyContent: 'center',
                                          borderStyle: 'dashed',
                                          borderWidth: '1px',
                                          backgroundColor: snapshot.isDraggingOver ? 'rgba(25, 118, 210, 0.04)' : 'transparent'
                                        }}>
                                          <Typography color="text.secondary">Drop a meal here</Typography>
                                        </Card>
                                      )}
                                      {lunchProvided.placeholder}
                                    </Box>
                                  )}
                                </Droppable>
                              </Grid>
                              
                              <Grid item xs={12} md={4}>
                                <Typography variant="h6" gutterBottom>Dinner</Typography>
                                <Droppable 
                                  droppableId={`meal-${dayPlan.dayNumber}-dinner`} 
                                  type="meals"
                                >
                                  {(dinnerProvided, snapshot) => (
                                    <Box
                                      ref={dinnerProvided.innerRef}
                                      {...dinnerProvided.droppableProps}
                                      sx={{ 
                                        minHeight: '200px', 
                                        backgroundColor: snapshot.isDraggingOver ? 'rgba(25, 118, 210, 0.08)' : 'transparent',
                                        transition: 'all 0.2s ease',
                                        borderRadius: 1,
                                        border: snapshot.isDraggingOver ? '2px dashed #1976d2' : '2px dashed transparent',
                                        padding: 1
                                      }}
                                      aria-label={`Drop zone for dinner on ${dayPlan.day}`}
                                    >
                                      {dayPlan.meals.dinner && (
                                        <Draggable 
                                          draggableId={`meal-${dayPlan.dayNumber}-dinner-${dayPlan.meals.dinner.id}`}
                                          index={0}
                                        >
                                          {(mealProvided) => (
                                            <div
                                              ref={mealProvided.innerRef}
                                              {...mealProvided.draggableProps}
                                              {...mealProvided.dragHandleProps}
                                              style={{
                                                ...mealProvided.draggableProps.style,
                                                cursor: 'grab'
                                              }}
                                              aria-label={`Drag ${dayPlan.meals.dinner?.name} to move to another slot`}
                                            >
                                              {renderMealCard(dayPlan.meals.dinner, dayPlan.dayNumber, 'dinner')}
                                            </div>
                                          )}
                                        </Draggable>
                                      )}
                                      {!dayPlan.meals.dinner && (
                                        <Card variant="outlined" sx={{ 
                                          height: '100%', 
                                          minHeight: '100px', 
                                          display: 'flex', 
                                          alignItems: 'center', 
                                          justifyContent: 'center',
                                          borderStyle: 'dashed',
                                          borderWidth: '1px',
                                          backgroundColor: snapshot.isDraggingOver ? 'rgba(25, 118, 210, 0.04)' : 'transparent'
                                        }}>
                                          <Typography color="text.secondary">Drop a meal here</Typography>
                                        </Card>
                                      )}
                                      {dinnerProvided.placeholder}
                                    </Box>
                                  )}
                                </Droppable>
                              </Grid>
                            </Grid>
                          </Paper>
                        </Box>
                      )}
                    </Draggable>
                  ))}
                  {provided.placeholder}
                </Box>
              )}
            </Droppable>
          </DragDropContext>
        </>
      )}

      {/* Undo Snackbar */}
      <Snackbar
        open={showUndoSnackbar}
        autoHideDuration={6000}
        onClose={handleCloseUndoSnackbar}
        message="Meal plan updated"
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
        action={
          <Button 
            color="primary" 
            size="small"
            onClick={handleUndoChange}
            startIcon={<UndoIcon />}
          >
            UNDO
          </Button>
        }
      />
    </Container>
  );
};

export default MealPlanner;
