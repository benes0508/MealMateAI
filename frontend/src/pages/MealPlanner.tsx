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
  TextField,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Paper,
  InputAdornment,
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
  Snackbar
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
  Code as CodeIcon
} from '@mui/icons-material';
import { DragDropContext, Droppable, Draggable, DropResult, DroppableProvided } from 'react-beautiful-dnd';
import { getMealPlan, generateMealPlan, generateMealPlanFromText, editMealPlanWithText, getUserMealPlans, getGroceryList, moveMeal, swapDays, createMockMealPlan } from '../services/mealPlannerService';

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
  
  // Text prompt dialog
  const [showTextPromptDialog, setShowTextPromptDialog] = useState<boolean>(false);
  const [textPrompt, setTextPrompt] = useState<string>('');
  const [isSubmittingPrompt, setIsSubmittingPrompt] = useState<boolean>(false);
  
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
  const fetchGroceryList = async (mealPlanId: number) => {
    if (!mealPlanId) return;
    
    setLoadingGroceryList(true);
    try {
      const data = await getGroceryList(mealPlanId);
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
    if (!showGroceryList && selectedMealPlanId && !groceryList) {
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
    
    // Convert the map to an array
    return Array.from(dayMap.values());
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

  const handleOpenTextPromptDialog = () => {
    setTextPrompt('');
    setShowTextPromptDialog(true);
  };

  const handleCloseTextPromptDialog = () => {
    setShowTextPromptDialog(false);
  };

  const handleTextPromptChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setTextPrompt(e.target.value);
  };

  const handleGenerateFromText = async () => {
    if (!textPrompt.trim()) {
      return;
    }

    setIsSubmittingPrompt(true);
    setError(null);
    setShowTextPromptDialog(false);
    setLoading(true); // Start loading state for the main UI
    
    try {
      let data;
      
      if (selectedMealPlanId) {
        // Edit existing meal plan
        console.log(`Editing meal plan ${selectedMealPlanId} with feedback: "${textPrompt}"`);
        data = await editMealPlanWithText(selectedMealPlanId, textPrompt);
        console.log("Raw edited meal plan data:", data);
      } else {
        // Create new meal plan
        console.log(`Creating new meal plan with prompt: "${textPrompt}"`);
        data = await generateMealPlanFromText(textPrompt);
        console.log("Raw text-generated meal plan data:", data);
      }
      
      const transformedData = transformMealPlanData(data);
      console.log("Transformed meal plan data:", transformedData);
      setMealPlan(transformedData);
      
      // Update the current meal plan metadata
      if (data) {
        setCurrentMealPlanMetadata({
          id: data.id,
          name: data.plan_name,
          explanation: data.plan_explanation,
          createdAt: data.created_at,
          days: data.days,
          mealsPerDay: data.meals_per_day
        });
        
        // If we were editing, update the selected meal plan ID
        if (selectedMealPlanId && data.id !== selectedMealPlanId) {
          setSelectedMealPlanId(data.id);
        }
      }
      
    } catch (err) {
      const action = selectedMealPlanId ? 'edit' : 'generate';
      setError(`Failed to ${action} a meal plan from your text prompt. Please try again.`);
      console.error(err);
    } finally {
      setIsSubmittingPrompt(false);
      setLoading(false); // End loading state
    }
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

  // Function to load a mock meal plan for development/testing
  const handleLoadMockMealPlan = () => {
    setLoading(true);
    setError(null);
    
    try {
      // Get mock data
      const mockData = createMockMealPlan();
      
      // Set metadata
      setCurrentMealPlanMetadata({
        id: mockData.id,
        plan_name: mockData.plan_name,
        created_at: mockData.created_at,
        days: mockData.days,
        meals_per_day: mockData.meals_per_day,
        plan_explanation: mockData.plan_explanation
      });
      
      // Transform and set meal plan data
      const transformedData = transformMealPlanData(mockData);
      console.log("Mock meal plan loaded:", transformedData);
      setMealPlan(transformedData);
      
    } catch (err) {
      setError('Failed to load mock meal plan.');
      console.error(err);
    } finally {
      setLoading(false);
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
      const day1 = parseInt(source.droppableId.split('-')[1]);
      const day2 = parseInt(destination.droppableId.split('-')[1]);
      
      // Update UI optimistically
      const newMealPlan = [...mealPlan];
      const [movedDay] = newMealPlan.splice(source.index, 1);
      newMealPlan.splice(destination.index, 0, movedDay);
      setMealPlan(newMealPlan);
      
      // Call API to make the change permanent
      if (selectedMealPlanId) {
        setMovingMeal(true);
        try {
          await swapDays(selectedMealPlanId, day1, day2);
          setShowUndoSnackbar(true);
        } catch (err) {
          console.error('Error swapping days:', err);
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
      
      // Update source and destination meals
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
            destMealType
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

  const renderMealCard = (meal: Meal | undefined) => {
    if (!meal) return <Typography color="text.secondary">No meal planned</Typography>;
    
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
            variant="outlined" 
            color="primary"
            onClick={handleOpenTextPromptDialog}
            disabled={loading}
            startIcon={<RestaurantIcon />}
          >
            {selectedMealPlanId ? 'Edit with Text' : 'Create with Text'}
          </Button>
          <Button 
            variant="contained" 
            color="primary"
            onClick={handleGenerateNewPlan}
            disabled={loading}
          >
            Generate New Plan
          </Button>
          <Button
            variant="outlined"
            color="secondary"
            onClick={handleLoadMockMealPlan}
            disabled={loading}
            startIcon={<CodeIcon />}
            title="For development/testing only"
          >
            Load Mock Data
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
            <Box sx={{ mt: 2 }}>
              <Button
                variant="outlined"
                color="primary"
                startIcon={<RestaurantIcon />}
                onClick={handleOpenTextPromptDialog}
              >
                Or create with a custom text prompt
              </Button>
              <Button
                variant="outlined"
                color="secondary"
                onClick={handleLoadMockMealPlan}
                sx={{ mt: 1 }}
                startIcon={<CodeIcon />}
              >
                Load Mock Data (For Testing)
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
                  <Button
                    variant="outlined"
                    color="primary"
                    size="small"
                    startIcon={<ShoppingCartIcon />}
                    onClick={handleToggleGroceryList}
                  >
                    {showGroceryList ? 'Hide Grocery List' : 'Show Grocery List'}
                  </Button>
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
                  <Box sx={{ display: 'flex', justifyContent: 'center', py: 2 }}>
                    <CircularProgress size={24} />
                  </Box>
                ) : groceryList && groceryList.items && groceryList.items.length > 0 ? (
                  <Box>
                    {/* Group by category */}
                    {Object.entries(
                      groceryList.items.reduce((acc: Record<string, GroceryItem[]>, item) => {
                        const category = item.category || 'Other';
                        if (!acc[category]) acc[category] = [];
                        acc[category].push(item);
                        return acc;
                      }, {} as Record<string, GroceryItem[]>)
                    ).map(([category, items]) => (
                      <Box key={category} sx={{ mb: 2 }}>
                        <Typography variant="subtitle1" gutterBottom sx={{ fontWeight: 'bold' }}>
                          {category}
                        </Typography>
                        <List dense>
                          {items.map((item, idx) => (
                            <ListItem key={idx} divider={idx < items.length - 1}>
                              <ListItemText 
                                primary={item.name}
                                secondary={item.quantity}
                              />
                            </ListItem>
                          ))}
                        </List>
                      </Box>
                    ))}
                  </Box>
                ) : (
                  <Typography variant="body1" color="text.secondary">
                    No grocery list available for this meal plan.
                  </Typography>
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
                                              {renderMealCard(dayPlan.meals.breakfast)}
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
                                              {renderMealCard(dayPlan.meals.lunch)}
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
                                              {renderMealCard(dayPlan.meals.dinner)}
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

      <Dialog
        open={showTextPromptDialog}
        onClose={handleCloseTextPromptDialog}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>
          {selectedMealPlanId ? 'Edit Meal Plan with Text' : 'Generate Meal Plan from Text Prompt'}
          <IconButton
            edge="end"
            color="inherit"
            onClick={handleCloseTextPromptDialog}
            aria-label="close"
            sx={{ position: 'absolute', right: 8, top: 8 }}
          >
            <CloseIcon />
          </IconButton>
        </DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" paragraph>
            {selectedMealPlanId 
              ? 'Describe what you want to change about your current meal plan. Be as specific as possible.'
              : 'Enter a description of your desired meal plan. Be as detailed as possible.'
            }
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2, fontStyle: 'italic' }}>
            {selectedMealPlanId 
              ? 'Example: "Replace all breakfast items with high-protein options" or "Make day 3 and 4 vegetarian" or "Add more Mediterranean dishes"'
              : 'Example: "I need a 7-day vegetarian meal plan with high protein options. I\'m allergic to nuts and prefer Mediterranean-style cooking."'
            }
          </Typography>
          <TextField
            autoFocus
            margin="dense"
            label="Text Prompt"
            multiline
            rows={4}
            fullWidth
            variant="outlined"
            value={textPrompt}
            onChange={handleTextPromptChange}
            placeholder={selectedMealPlanId ? "I want to change..." : "I need a meal plan that..."}
            InputProps={{
              endAdornment: textPrompt ? (
                <InputAdornment position="end">
                  <IconButton
                    edge="end"
                    color="inherit"
                    onClick={() => setTextPrompt('')}
                    aria-label="clear"
                  >
                    <CloseIcon />
                  </IconButton>
                </InputAdornment>
              ) : null,
            }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseTextPromptDialog} color="primary">
            Cancel
          </Button>
          <Button 
            onClick={handleGenerateFromText} 
            color="primary" 
            disabled={isSubmittingPrompt || !textPrompt.trim()}
          >
            {isSubmittingPrompt ? <CircularProgress size={24} /> : (selectedMealPlanId ? 'Edit Plan' : 'Generate Plan')}
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default MealPlanner;
