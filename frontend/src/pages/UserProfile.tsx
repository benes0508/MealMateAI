import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Container,
  Grid,
  Typography,
  Box,
  TextField,
  Button,
  Paper,
  Divider,
  FormControl,
  FormControlLabel,
  FormGroup,
  FormLabel,
  Checkbox,
  Chip,
  Avatar,
  Alert,
  Tabs,
  Tab,
  CircularProgress,
  InputAdornment,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions
} from '@mui/material';
import {
  Save as SaveIcon,
  Add as AddIcon,
  Delete as DeleteIcon,
  Visibility as VisibilityIcon,
  VisibilityOff as VisibilityOffIcon
} from '@mui/icons-material';
import { useAuth } from '../context/AuthContext';
import authService from '../services/authService';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`profile-tabpanel-${index}`}
      aria-labelledby={`profile-tab-${index}`}
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

interface UserPreferences {
  allergies: string[];
  disliked_ingredients: string[];
  preferred_cuisines: string[];
  preferences: {
    dietary_restrictions?: string[];
    cooking_skill?: string;
    meal_prep_time?: string;
  };
}

interface UpdateProfileData {
  name?: string;
  email?: string;
  current_password?: string;
  new_password?: string;
}

const UserProfile = () => {
  const { user, setUser } = useAuth();
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState(0);
  const [loading, setLoading] = useState(true);
  const [saveLoading, setSaveLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);

  // Profile state
  const [profileData, setProfileData] = useState<UpdateProfileData>({
    name: '',
    email: '',
    current_password: '',
    new_password: ''
  });
  
  // Password visibility
  const [showPassword, setShowPassword] = useState({
    current: false,
    new: false
  });

  // Preferences state
  const [preferences, setPreferences] = useState<UserPreferences>({
    allergies: [],
    disliked_ingredients: [],
    preferred_cuisines: [],
    preferences: {
      dietary_restrictions: [],
      cooking_skill: 'intermediate',
      meal_prep_time: '30-60min'
    }
  });

  // New ingredient input states
  const [newAllergy, setNewAllergy] = useState('');
  const [newDislikedIngredient, setNewDislikedIngredient] = useState('');
  const [newPreferredCuisine, setNewPreferredCuisine] = useState('');

  useEffect(() => {
    if (!user) {
      navigate('/login');
      return;
    }

    const fetchUserProfile = async () => {
      try {
        setLoading(true);
        setError(null);
        
        const data = await authService.getUserProfile(user.id);
        
        // Set profile data
        setProfileData({
          name: data.user.name,
          email: data.user.email,
          current_password: '',
          new_password: ''
        });
        
        // Set preferences
        setPreferences({
          allergies: data.preferences.allergies || [],
          disliked_ingredients: data.preferences.disliked_ingredients || [],
          preferred_cuisines: data.preferences.preferred_cuisines || [],
          preferences: data.preferences.preferences || {
            dietary_restrictions: [],
            cooking_skill: 'intermediate',
            meal_prep_time: '30-60min'
          }
        });
        
      } catch (err) {
        console.error('Failed to fetch user profile:', err);
        setError('Failed to load user profile. Please try again.');
      } finally {
        setLoading(false);
      }
    };

    fetchUserProfile();
  }, [user, navigate]);

  // Handle tab change
  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };

  // Handle profile form changes
  const handleProfileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setProfileData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  // Handle dietary restriction changes
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

  // Handle cooking skill and meal prep time changes
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

  // Save profile changes
  const handleSaveProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Only submit fields with values
    const dataToSubmit: UpdateProfileData = {};
    if (profileData.name !== user?.name) dataToSubmit.name = profileData.name;
    if (profileData.email !== user?.email) dataToSubmit.email = profileData.email;
    if (profileData.current_password) dataToSubmit.current_password = profileData.current_password;
    if (profileData.new_password) dataToSubmit.new_password = profileData.new_password;

    // Don't submit if nothing changed
    if (Object.keys(dataToSubmit).length === 0) {
      setSuccess('No changes to save');
      setTimeout(() => setSuccess(null), 3000);
      return;
    }

    // Validate password change
    if (profileData.new_password && !profileData.current_password) {
      setError('Current password is required to set a new password');
      return;
    }

    try {
      setSaveLoading(true);
      setError(null);
      
      const updatedUser = await authService.updateUserProfile(user!.id, dataToSubmit);
      
      // Update context with new user data
      setUser({
        ...user!,
        name: updatedUser.name,
        email: updatedUser.email
      });
      
      // Reset password fields
      setProfileData(prev => ({
        ...prev,
        current_password: '',
        new_password: ''
      }));
      
      setSuccess('Profile updated successfully');
      setTimeout(() => setSuccess(null), 3000);
      
    } catch (err: any) {
      console.error('Failed to update profile:', err);
      setError(err.response?.data?.message || 'Failed to update profile. Please try again.');
    } finally {
      setSaveLoading(false);
    }
  };

  // Save preferences changes
  const handleSavePreferences = async (e: React.FormEvent) => {
    e.preventDefault();
    
    try {
      setSaveLoading(true);
      setError(null);
      
      await authService.updateUserPreferences(user!.id, preferences);
      
      setSuccess('Preferences updated successfully');
      setTimeout(() => setSuccess(null), 3000);
      
    } catch (err: any) {
      console.error('Failed to update preferences:', err);
      setError(err.response?.data?.message || 'Failed to update preferences. Please try again.');
    } finally {
      setSaveLoading(false);
    }
  };

  // Delete account handler
  const handleDeleteAccount = async () => {
    try {
      await authService.deleteAccount(user!.id);
      authService.logout();
      navigate('/login');
    } catch (err) {
      console.error('Failed to delete account:', err);
      setError('Failed to delete account. Please try again.');
    } finally {
      setShowDeleteDialog(false);
    }
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '60vh' }}>
        <CircularProgress />
      </Box>
    );
  }

  // Is restriction selected
  const isRestrictionSelected = (restriction: string): boolean => {
    return (preferences.preferences.dietary_restrictions || []).includes(restriction);
  };

  return (
    <Container maxWidth="md" sx={{ mt: 4, mb: 8 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        Your Profile
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {success && (
        <Alert severity="success" sx={{ mb: 2 }}>
          {success}
        </Alert>
      )}

      <Paper sx={{ borderRadius: 1 }}>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs value={activeTab} onChange={handleTabChange} aria-label="profile tabs">
            <Tab label="Account Settings" />
            <Tab label="Food Preferences" />
          </Tabs>
        </Box>
        
        {/* Account Settings Tab */}
        <TabPanel value={activeTab} index={0}>
          <Box component="form" onSubmit={handleSaveProfile}>
            <Grid container spacing={3}>
              <Grid item xs={12} display="flex" justifyContent="center">
                <Avatar 
                  sx={{ 
                    width: 100, 
                    height: 100, 
                    bgcolor: 'primary.main',
                    fontSize: '2rem'
                  }}
                >
                  {profileData.name?.charAt(0) || 'U'}
                </Avatar>
              </Grid>
              
              <Grid item xs={12} sm={6}>
                <TextField
                  name="name"
                  label="Full Name"
                  fullWidth
                  value={profileData.name}
                  onChange={handleProfileChange}
                  required
                />
              </Grid>
              
              <Grid item xs={12} sm={6}>
                <TextField
                  name="email"
                  label="Email"
                  type="email"
                  fullWidth
                  value={profileData.email}
                  onChange={handleProfileChange}
                  required
                />
              </Grid>
              
              <Grid item xs={12}>
                <Divider sx={{ my: 1 }}>
                  <Typography variant="body2" color="text.secondary">
                    Change Password
                  </Typography>
                </Divider>
              </Grid>
              
              <Grid item xs={12} sm={6}>
                <TextField
                  name="current_password"
                  label="Current Password"
                  type={showPassword.current ? 'text' : 'password'}
                  fullWidth
                  value={profileData.current_password}
                  onChange={handleProfileChange}
                  InputProps={{
                    endAdornment: (
                      <InputAdornment position="end">
                        <IconButton
                          onClick={() => setShowPassword(prev => ({ ...prev, current: !prev.current }))}
                          edge="end"
                        >
                          {showPassword.current ? <VisibilityOffIcon /> : <VisibilityIcon />}
                        </IconButton>
                      </InputAdornment>
                    )
                  }}
                />
              </Grid>
              
              <Grid item xs={12} sm={6}>
                <TextField
                  name="new_password"
                  label="New Password"
                  type={showPassword.new ? 'text' : 'password'}
                  fullWidth
                  value={profileData.new_password}
                  onChange={handleProfileChange}
                  InputProps={{
                    endAdornment: (
                      <InputAdornment position="end">
                        <IconButton
                          onClick={() => setShowPassword(prev => ({ ...prev, new: !prev.new }))}
                          edge="end"
                        >
                          {showPassword.new ? <VisibilityOffIcon /> : <VisibilityIcon />}
                        </IconButton>
                      </InputAdornment>
                    )
                  }}
                />
              </Grid>
              
              <Grid item xs={12} display="flex" justifyContent="space-between">
                <Button 
                  variant="outlined" 
                  color="error"
                  onClick={() => setShowDeleteDialog(true)}
                >
                  Delete Account
                </Button>
                
                <Button
                  type="submit"
                  variant="contained"
                  startIcon={<SaveIcon />}
                  disabled={saveLoading}
                >
                  {saveLoading ? 'Saving...' : 'Save Changes'}
                </Button>
              </Grid>
            </Grid>
          </Box>
        </TabPanel>
        
        {/* Preferences Tab */}
        <TabPanel value={activeTab} index={1}>
          <Box component="form" onSubmit={handleSavePreferences}>
            <Grid container spacing={3}>
              <Grid item xs={12}>
                <FormControl component="fieldset">
                  <FormLabel component="legend">Dietary Restrictions</FormLabel>
                  <FormGroup row>
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
              </Grid>
              
              <Grid item xs={12}>
                <Divider />
              </Grid>

              <Grid item xs={12} sm={6}>
                <TextField
                  name="cooking_skill"
                  label="Cooking Skill Level"
                  select
                  fullWidth
                  value={preferences.preferences.cooking_skill || 'intermediate'}
                  onChange={handlePreferenceChange}
                  SelectProps={{
                    native: true
                  }}
                >
                  <option value="beginner">Beginner</option>
                  <option value="intermediate">Intermediate</option>
                  <option value="advanced">Advanced</option>
                </TextField>
              </Grid>
              
              <Grid item xs={12} sm={6}>
                <TextField
                  name="meal_prep_time"
                  label="Preferred Meal Prep Time"
                  select
                  fullWidth
                  value={preferences.preferences.meal_prep_time || '30-60min'}
                  onChange={handlePreferenceChange}
                  SelectProps={{
                    native: true
                  }}
                >
                  <option value="under-15min">Under 15 minutes</option>
                  <option value="15-30min">15-30 minutes</option>
                  <option value="30-60min">30-60 minutes</option>
                  <option value="over-60min">Over 60 minutes</option>
                </TextField>
              </Grid>
              
              <Grid item xs={12}>
                <Divider />
              </Grid>
              
              {/* Allergies Section */}
              <Grid item xs={12}>
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
                
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
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
                      No allergies added.
                    </Typography>
                  )}
                </Box>
              </Grid>
              
              {/* Disliked Ingredients Section */}
              <Grid item xs={12}>
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
                
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
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
                      No disliked ingredients added.
                    </Typography>
                  )}
                </Box>
              </Grid>
              
              {/* Preferred Cuisines Section */}
              <Grid item xs={12}>
                <Typography variant="subtitle1" gutterBottom>
                  Preferred Cuisines
                </Typography>
                
                <Box component="form" onSubmit={handleAddPreferredCuisine} sx={{ display: 'flex', mb: 2 }}>
                  <TextField 
                    value={newPreferredCuisine}
                    onChange={(e) => setNewPreferredCuisine(e.target.value)}
                    placeholder="Add a preferred cuisine"
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
                
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                  {preferences.preferred_cuisines.length > 0 ? (
                    preferences.preferred_cuisines.map((cuisine, index) => (
                      <Chip
                        key={index}
                        label={cuisine}
                        onDelete={() => handleRemovePreferredCuisine(cuisine)}
                        color="primary"
                        variant="outlined"
                      />
                    ))
                  ) : (
                    <Typography variant="body2" color="text.secondary">
                      No preferred cuisines added.
                    </Typography>
                  )}
                </Box>
              </Grid>
              
              <Grid item xs={12} display="flex" justifyContent="flex-end">
                <Button
                  type="submit"
                  variant="contained"
                  startIcon={<SaveIcon />}
                  disabled={saveLoading}
                >
                  {saveLoading ? 'Saving...' : 'Save Preferences'}
                </Button>
              </Grid>
            </Grid>
          </Box>
        </TabPanel>
      </Paper>

      {/* Delete Account Confirmation Dialog */}
      <Dialog
        open={showDeleteDialog}
        onClose={() => setShowDeleteDialog(false)}
      >
        <DialogTitle>Delete Account</DialogTitle>
        <DialogContent>
          <DialogContentText>
            Are you sure you want to delete your account? This action cannot be undone.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowDeleteDialog(false)}>Cancel</Button>
          <Button onClick={handleDeleteAccount} color="error">
            Delete
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default UserProfile;