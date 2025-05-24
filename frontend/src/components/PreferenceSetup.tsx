import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Container,
  Typography,
  Paper,
  Stepper,
  Step,
  StepLabel,
  Button,
  FormControl,
  FormControlLabel,
  FormGroup,
  FormLabel,
  Checkbox,
  TextField,
  Grid,
  Chip,
  Divider,
  CircularProgress,
  Alert
} from '@mui/material';
import {
  Add as AddIcon
} from '@mui/icons-material';
import { useAuth } from '../context/AuthContext';
import authService from '../services/authService';

const steps = ['Dietary Restrictions', 'Allergies & Dislikes', 'Cuisine Preferences'];

const PreferenceSetup = () => {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [activeStep, setActiveStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Preferences state
  const [preferences, setPreferences] = useState({
    allergies: [] as string[],
    disliked_ingredients: [] as string[],
    preferred_cuisines: [] as string[],
    preferences: {
      dietary_restrictions: [] as string[],
      cooking_skill: 'intermediate',
      meal_prep_time: '30-60min'
    }
  });

  // New item inputs
  const [newAllergy, setNewAllergy] = useState('');
  const [newDislikedIngredient, setNewDislikedIngredient] = useState('');
  const [newPreferredCuisine, setNewPreferredCuisine] = useState('');

  const handleNext = () => {
    setActiveStep((prevStep) => prevStep + 1);
  };

  const handleBack = () => {
    setActiveStep((prevStep) => prevStep - 1);
  };

  const handleSkip = () => {
    // Navigate to dashboard or home page
    navigate('/dashboard');
  };

  const handleDietaryChange = (restriction: string) => (e: React.ChangeEvent<HTMLInputElement>) => {
    const { checked } = e.target;
    setPreferences(prev => {
      const currentRestrictions = prev.preferences.dietary_restrictions || [];
      
      let updatedRestrictions;
      if (checked) {
        updatedRestrictions = [...currentRestrictions, restriction];
      } else {
        updatedRestrictions = currentRestrictions.filter(item => item !== restriction);
      }
      
      return {
        ...prev,
        preferences: {
          ...prev.preferences,
          dietary_restrictions: updatedRestrictions
        }
      };
    });
  };

  const handlePreferenceChange = (e: React.ChangeEvent<HTMLInputElement | { name?: string; value: unknown }>) => {
    const { name, value } = e.target;
    if (!name) return;
    
    setPreferences(prev => ({
      ...prev,
      preferences: {
        ...prev.preferences,
        [name]: value as string
      }
    }));
  };

  // Add a new allergy
  const handleAddAllergy = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newAllergy.trim()) return;
    
    setPreferences(prev => ({
      ...prev,
      allergies: [...prev.allergies, newAllergy.trim()]
    }));
    setNewAllergy('');
  };

  // Add a new disliked ingredient
  const handleAddDislikedIngredient = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newDislikedIngredient.trim()) return;
    
    setPreferences(prev => ({
      ...prev,
      disliked_ingredients: [...prev.disliked_ingredients, newDislikedIngredient.trim()]
    }));
    setNewDislikedIngredient('');
  };

  // Add a new preferred cuisine
  const handleAddPreferredCuisine = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newPreferredCuisine.trim()) return;
    
    setPreferences(prev => ({
      ...prev,
      preferred_cuisines: [...prev.preferred_cuisines, newPreferredCuisine.trim()]
    }));
    setNewPreferredCuisine('');
  };

  // Remove an allergy
  const handleRemoveAllergy = (allergy: string) => {
    setPreferences(prev => ({
      ...prev,
      allergies: prev.allergies.filter(a => a !== allergy)
    }));
  };

  // Remove a disliked ingredient
  const handleRemoveDislikedIngredient = (ingredient: string) => {
    setPreferences(prev => ({
      ...prev,
      disliked_ingredients: prev.disliked_ingredients.filter(i => i !== ingredient)
    }));
  };

  // Remove a preferred cuisine
  const handleRemovePreferredCuisine = (cuisine: string) => {
    setPreferences(prev => ({
      ...prev,
      preferred_cuisines: prev.preferred_cuisines.filter(c => c !== cuisine)
    }));
  };

  const handleSubmit = async () => {
    if (!user) {
      navigate('/login');
      return;
    }
    
    try {
      setLoading(true);
      setError(null);
      
      await authService.updateUserPreferences(user.id, preferences);
      
      // Navigate to the dashboard after successful completion
      navigate('/dashboard');
      
    } catch (err: any) {
      console.error('Failed to save preferences:', err);
      setError(err.response?.data?.message || 'Failed to save preferences. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  // Is restriction selected
  const isRestrictionSelected = (restriction: string): boolean => {
    return (preferences.preferences.dietary_restrictions || []).includes(restriction);
  };

  return (
    <Container maxWidth="md" sx={{ py: 4 }}>
      <Paper sx={{ p: 4, borderRadius: 2 }}>
        <Typography variant="h4" component="h1" align="center" gutterBottom>
          Set Up Your Preferences
        </Typography>
        
        <Typography variant="body1" align="center" color="text.secondary" paragraph>
          Help us personalize your meal planning experience
        </Typography>

        <Stepper activeStep={activeStep} sx={{ mb: 4 }}>
          {steps.map((label) => (
            <Step key={label}>
              <StepLabel>{label}</StepLabel>
            </Step>
          ))}
        </Stepper>

        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        {/* Step content */}
        <Box sx={{ mt: 2, mb: 4 }}>
          {activeStep === 0 && (
            // Dietary Restrictions Step
            <Box>
              <Typography variant="h6" gutterBottom>
                Do you have any dietary restrictions?
              </Typography>
              
              <FormControl component="fieldset" sx={{ width: '100%' }}>
                <FormGroup>
                  <Grid container spacing={2}>
                    <Grid item xs={6} sm={4}>
                      <FormControlLabel
                        control={
                          <Checkbox
                            checked={isRestrictionSelected('vegetarian')}
                            onChange={handleDietaryChange('vegetarian')}
                            name="vegetarian"
                          />
                        }
                        label="Vegetarian"
                      />
                    </Grid>
                    <Grid item xs={6} sm={4}>
                      <FormControlLabel
                        control={
                          <Checkbox
                            checked={isRestrictionSelected('vegan')}
                            onChange={handleDietaryChange('vegan')}
                            name="vegan"
                          />
                        }
                        label="Vegan"
                      />
                    </Grid>
                    <Grid item xs={6} sm={4}>
                      <FormControlLabel
                        control={
                          <Checkbox
                            checked={isRestrictionSelected('gluten-free')}
                            onChange={handleDietaryChange('gluten-free')}
                            name="gluten-free"
                          />
                        }
                        label="Gluten-Free"
                      />
                    </Grid>
                    <Grid item xs={6} sm={4}>
                      <FormControlLabel
                        control={
                          <Checkbox
                            checked={isRestrictionSelected('dairy-free')}
                            onChange={handleDietaryChange('dairy-free')}
                            name="dairy-free"
                          />
                        }
                        label="Dairy-Free"
                      />
                    </Grid>
                    <Grid item xs={6} sm={4}>
                      <FormControlLabel
                        control={
                          <Checkbox
                            checked={isRestrictionSelected('nut-free')}
                            onChange={handleDietaryChange('nut-free')}
                            name="nut-free"
                          />
                        }
                        label="Nut-Free"
                      />
                    </Grid>
                    <Grid item xs={6} sm={4}>
                      <FormControlLabel
                        control={
                          <Checkbox
                            checked={isRestrictionSelected('keto')}
                            onChange={handleDietaryChange('keto')}
                            name="keto"
                          />
                        }
                        label="Keto"
                      />
                    </Grid>
                    <Grid item xs={6} sm={4}>
                      <FormControlLabel
                        control={
                          <Checkbox
                            checked={isRestrictionSelected('paleo')}
                            onChange={handleDietaryChange('paleo')}
                            name="paleo"
                          />
                        }
                        label="Paleo"
                      />
                    </Grid>
                  </Grid>
                </FormGroup>
              </FormControl>

              <Divider sx={{ my: 3 }} />
              
              <Grid container spacing={3}>
                <Grid item xs={12} sm={6}>
                  <TextField
                    name="cooking_skill"
                    label="Your Cooking Skill Level"
                    select
                    fullWidth
                    value={preferences.preferences.cooking_skill || 'intermediate'}
                    onChange={handlePreferenceChange}
                    SelectProps={{
                      native: true
                    }}
                    helperText="This helps us suggest recipes appropriate for your skill level"
                  >
                    <option value="beginner">Beginner</option>
                    <option value="intermediate">Intermediate</option>
                    <option value="advanced">Advanced</option>
                  </TextField>
                </Grid>
                
                <Grid item xs={12} sm={6}>
                  <TextField
                    name="meal_prep_time"
                    label="How much time do you have for cooking?"
                    select
                    fullWidth
                    value={preferences.preferences.meal_prep_time || '30-60min'}
                    onChange={handlePreferenceChange}
                    SelectProps={{
                      native: true
                    }}
                    helperText="We'll suggest recipes that match your time constraints"
                  >
                    <option value="under-15min">Under 15 minutes</option>
                    <option value="15-30min">15-30 minutes</option>
                    <option value="30-60min">30-60 minutes</option>
                    <option value="over-60min">Over 60 minutes</option>
                  </TextField>
                </Grid>
              </Grid>
            </Box>
          )}

          {activeStep === 1 && (
            // Allergies and Dislikes Step
            <Box>
              <Typography variant="h6" gutterBottom>
                Any allergies or ingredients you dislike?
              </Typography>
              
              <Grid container spacing={4}>
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle1" gutterBottom>
                    Allergies
                  </Typography>
                  
                  <Box component="form" onSubmit={handleAddAllergy} sx={{ display: 'flex', mb: 2 }}>
                    <TextField 
                      value={newAllergy}
                      onChange={(e) => setNewAllergy(e.target.value)}
                      placeholder="Add an allergy"
                      fullWidth
                      size="small"
                      variant="outlined"
                    />
                    <Button 
                      type="submit" 
                      variant="contained" 
                      startIcon={<AddIcon />} 
                      sx={{ ml: 1 }}
                      disabled={!newAllergy.trim()}
                    >
                      Add
                    </Button>
                  </Box>
                  
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, minHeight: '100px' }}>
                    {preferences.allergies.length > 0 ? (
                      preferences.allergies.map((allergy, index) => (
                        <Chip
                          key={index}
                          label={allergy}
                          onDelete={() => handleRemoveAllergy(allergy)}
                          color="primary"
                          variant="outlined"
                        />
                      ))
                    ) : (
                      <Typography variant="body2" color="text.secondary">
                        No allergies added yet. Add any ingredients you're allergic to.
                      </Typography>
                    )}
                  </Box>
                </Grid>
                
                <Grid item xs={12} md={6}>
                  <Typography variant="subtitle1" gutterBottom>
                    Disliked Ingredients
                  </Typography>
                  
                  <Box component="form" onSubmit={handleAddDislikedIngredient} sx={{ display: 'flex', mb: 2 }}>
                    <TextField 
                      value={newDislikedIngredient}
                      onChange={(e) => setNewDislikedIngredient(e.target.value)}
                      placeholder="Add a disliked ingredient"
                      fullWidth
                      size="small"
                      variant="outlined"
                    />
                    <Button 
                      type="submit" 
                      variant="contained" 
                      startIcon={<AddIcon />} 
                      sx={{ ml: 1 }}
                      disabled={!newDislikedIngredient.trim()}
                    >
                      Add
                    </Button>
                  </Box>
                  
                  <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, minHeight: '100px' }}>
                    {preferences.disliked_ingredients.length > 0 ? (
                      preferences.disliked_ingredients.map((ingredient, index) => (
                        <Chip
                          key={index}
                          label={ingredient}
                          onDelete={() => handleRemoveDislikedIngredient(ingredient)}
                          color="primary"
                          variant="outlined"
                        />
                      ))
                    ) : (
                      <Typography variant="body2" color="text.secondary">
                        No disliked ingredients added yet. Add ingredients you want to avoid.
                      </Typography>
                    )}
                  </Box>
                </Grid>
              </Grid>
            </Box>
          )}

          {activeStep === 2 && (
            // Cuisine Preferences Step
            <Box>
              <Typography variant="h6" gutterBottom>
                What cuisines do you prefer?
              </Typography>
              
              <Box component="form" onSubmit={handleAddPreferredCuisine} sx={{ display: 'flex', mb: 3 }}>
                <TextField 
                  value={newPreferredCuisine}
                  onChange={(e) => setNewPreferredCuisine(e.target.value)}
                  placeholder="Add a cuisine (e.g., Italian, Japanese, Mexican)"
                  fullWidth
                  size="small"
                  variant="outlined"
                />
                <Button 
                  type="submit" 
                  variant="contained" 
                  startIcon={<AddIcon />} 
                  sx={{ ml: 1 }}
                  disabled={!newPreferredCuisine.trim()}
                >
                  Add
                </Button>
              </Box>
              
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, minHeight: '120px' }}>
                {preferences.preferred_cuisines.length > 0 ? (
                  preferences.preferred_cuisines.map((cuisine, index) => (
                    <Chip
                      key={index}
                      label={cuisine}
                      onDelete={() => handleRemovePreferredCuisine(cuisine)}
                      color="primary"
                      variant="outlined"
                      sx={{ m: 0.5 }}
                    />
                  ))
                ) : (
                  <Typography variant="body2" color="text.secondary">
                    No cuisines added yet. Add your favorite cuisines to get personalized recommendations.
                  </Typography>
                )}
              </Box>

              <Box sx={{ mt: 4 }}>
                <Typography variant="body1" paragraph>
                  Ready to complete your profile? Click "Finish" below to save your preferences.
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  You can always update these preferences later in your profile settings.
                </Typography>
              </Box>
            </Box>
          )}
        </Box>

        {/* Navigation buttons */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
          <Button
            color="inherit"
            onClick={activeStep === 0 ? handleSkip : handleBack}
            sx={{ mr: 1 }}
          >
            {activeStep === 0 ? 'Skip' : 'Back'}
          </Button>
          <Box>
            <Button
              variant="contained"
              onClick={activeStep === steps.length - 1 ? handleSubmit : handleNext}
              disabled={loading}
            >
              {activeStep === steps.length - 1 ? (
                loading ? <CircularProgress size={24} /> : 'Finish'
              ) : (
                'Next'
              )}
            </Button>
          </Box>
        </Box>
      </Paper>
    </Container>
  );
};

export default PreferenceSetup;