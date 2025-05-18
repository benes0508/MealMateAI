import React, { useState, useEffect } from 'react';
import { 
  Container, 
  Typography, 
  Box, 
  Grid, 
  Card, 
  CardContent, 
  Button,
  CircularProgress,
  Alert
} from '@mui/material';
import { getMealPlan, generateMealPlan } from '../services/mealPlannerService';

interface Meal {
  id: string;
  name: string;
  description: string;
  ingredients: string[];
  image_url?: string;
  meal_type: string;
}

interface DayPlan {
  day: string;
  meals: {
    breakfast?: Meal;
    lunch?: Meal;
    dinner?: Meal;
  };
}

const MealPlanner: React.FC = () => {
  const [mealPlan, setMealPlan] = useState<DayPlan[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchMealPlan();
  }, []);

  const fetchMealPlan = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getMealPlan();
      setMealPlan(data);
    } catch (err) {
      setError('Failed to load your meal plan. Please try again.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateNewPlan = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await generateMealPlan();
      setMealPlan(data);
    } catch (err) {
      setError('Failed to generate a new meal plan. Please try again.');
      console.error(err);
    } finally {
      setLoading(false);
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
            {meal.ingredients.map((ingredient, idx) => (
              <Typography component="li" variant="body2" key={idx}>
                {ingredient}
              </Typography>
            ))}
          </Box>
        </CardContent>
      </Card>
    );
  };

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Your Meal Plan
        </Typography>
        <Button 
          variant="contained" 
          color="primary"
          onClick={handleGenerateNewPlan}
          disabled={loading}
        >
          Generate New Plan
        </Button>
      </Box>

      {error && <Alert severity="error" sx={{ mb: 3 }}>{error}</Alert>}
      
      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
          <CircularProgress />
        </Box>
      ) : mealPlan.length === 0 ? (
        <Alert severity="info">
          You don't have any meal plans yet. Generate a new plan to get started!
        </Alert>
      ) : (
        mealPlan.map((dayPlan, idx) => (
          <Box key={idx} sx={{ mb: 4 }}>
            <Typography variant="h5" sx={{ mb: 2 }}>
              {dayPlan.day}
            </Typography>
            <Grid container spacing={3}>
              <Grid item xs={12} md={4}>
                <Typography variant="h6" gutterBottom>Breakfast</Typography>
                {renderMealCard(dayPlan.meals.breakfast)}
              </Grid>
              <Grid item xs={12} md={4}>
                <Typography variant="h6" gutterBottom>Lunch</Typography>
                {renderMealCard(dayPlan.meals.lunch)}
              </Grid>
              <Grid item xs={12} md={4}>
                <Typography variant="h6" gutterBottom>Dinner</Typography>
                {renderMealCard(dayPlan.meals.dinner)}
              </Grid>
            </Grid>
          </Box>
        ))
      )}
    </Container>
  );
};

export default MealPlanner;