import { useNavigate } from 'react-router-dom';
import { 
  Box, 
  Button, 
  Container, 
  Typography, 
  Grid, 
  Card, 
  CardContent, 
  CardMedia,
  Stack
} from '@mui/material';
import { 
  AccessTime as AccessTimeIcon,
  FoodBank as FoodBankIcon,
  ShoppingBasket as ShoppingBasketIcon,
  MenuBook as MenuBookIcon
} from '@mui/icons-material';
import { useAuth } from '../context/AuthContext';

const Home = () => {
  const navigate = useNavigate();
  const { isAuthenticated } = useAuth();
  
  return (
    <>
      {/* Hero section */}
      <Box 
        sx={{ 
          bgcolor: 'background.paper',
          pt: 8,
          pb: 6,
          textAlign: 'center'
        }}
      >
        <Container maxWidth="md">
          <Typography
            component="h1"
            variant="h2"
            color="primary"
            gutterBottom
            fontWeight="bold"
          >
            MealMateAI
          </Typography>
          <Typography variant="h5" color="text.secondary" paragraph>
            Your personal AI-powered meal planning assistant
          </Typography>
          <Typography variant="body1" color="text.secondary" paragraph sx={{ mb: 4 }}>
            Create personalized meal plans based on your dietary preferences, allergies,
            and ingredients you love or want to avoid. Let MealMateAI make healthy eating simple.
          </Typography>
          <Stack
            direction={{ xs: 'column', sm: 'row' }}
            spacing={2}
            justifyContent="center"
          >
            {isAuthenticated ? (
              <>
                <Button 
                  variant="contained" 
                  size="large"
                  onClick={() => navigate('/dashboard')}
                >
                  Go to Dashboard
                </Button>
                <Button 
                  variant="outlined" 
                  size="large"
                  onClick={() => navigate('/meal-planner')}
                >
                  Start Planning Meals
                </Button>
              </>
            ) : (
              <>
                <Button 
                  variant="contained" 
                  size="large"
                  onClick={() => navigate('/register')}
                >
                  Sign Up Free
                </Button>
                <Button 
                  variant="outlined" 
                  size="large"
                  onClick={() => navigate('/login')}
                >
                  Sign In
                </Button>
              </>
            )}
          </Stack>
        </Container>
      </Box>

      {/* Features section */}
      <Box sx={{ py: 8 }}>
        <Container maxWidth="lg">
          <Typography variant="h4" component="h2" gutterBottom textAlign="center" mb={6}>
            How It Works
          </Typography>
          <Grid container spacing={4}>
            {/* Feature 1 */}
            <Grid item xs={12} sm={6} md={3}>
              <Card
                sx={{
                  height: '100%',
                  display: 'flex',
                  flexDirection: 'column',
                  borderRadius: 2
                }}
                elevation={2}
              >
                <Box sx={{ p: 2, display: 'flex', justifyContent: 'center' }}>
                  <FoodBankIcon color="primary" sx={{ fontSize: 60 }} />
                </Box>
                <CardContent sx={{ flexGrow: 1 }}>
                  <Typography gutterBottom variant="h6" component="h2" align="center">
                    Personalize
                  </Typography>
                  <Typography align="center">
                    Tell us about your dietary needs, allergies, and food preferences
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            
            {/* Feature 2 */}
            <Grid item xs={12} sm={6} md={3}>
              <Card
                sx={{
                  height: '100%',
                  display: 'flex',
                  flexDirection: 'column',
                  borderRadius: 2
                }}
                elevation={2}
              >
                <Box sx={{ p: 2, display: 'flex', justifyContent: 'center' }}>
                  <MenuBookIcon color="primary" sx={{ fontSize: 60 }} />
                </Box>
                <CardContent sx={{ flexGrow: 1 }}>
                  <Typography gutterBottom variant="h6" component="h2" align="center">
                    Plan Meals
                  </Typography>
                  <Typography align="center">
                    Get AI-generated meal plans tailored to your specific needs
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            
            {/* Feature 3 */}
            <Grid item xs={12} sm={6} md={3}>
              <Card
                sx={{
                  height: '100%',
                  display: 'flex',
                  flexDirection: 'column',
                  borderRadius: 2
                }}
                elevation={2}
              >
                <Box sx={{ p: 2, display: 'flex', justifyContent: 'center' }}>
                  <ShoppingBasketIcon color="primary" sx={{ fontSize: 60 }} />
                </Box>
                <CardContent sx={{ flexGrow: 1 }}>
                  <Typography gutterBottom variant="h6" component="h2" align="center">
                    Get Groceries
                  </Typography>
                  <Typography align="center">
                    Generate shopping lists automatically from your meal plans
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
            
            {/* Feature 4 */}
            <Grid item xs={12} sm={6} md={3}>
              <Card
                sx={{
                  height: '100%',
                  display: 'flex',
                  flexDirection: 'column',
                  borderRadius: 2
                }}
                elevation={2}
              >
                <Box sx={{ p: 2, display: 'flex', justifyContent: 'center' }}>
                  <AccessTimeIcon color="primary" sx={{ fontSize: 60 }} />
                </Box>
                <CardContent sx={{ flexGrow: 1 }}>
                  <Typography gutterBottom variant="h6" component="h2" align="center">
                    Save Time
                  </Typography>
                  <Typography align="center">
                    Spend less time planning and more time enjoying healthy meals
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </Container>
      </Box>

      {/* Call to action section */}
      <Box sx={{ bgcolor: 'background.paper', py: 8 }}>
        <Container maxWidth="md">
          <Typography
            variant="h4"
            align="center"
            color="text.primary"
            gutterBottom
          >
            Ready to simplify your meal planning?
          </Typography>
          <Typography variant="body1" align="center" color="text.secondary" paragraph>
            Join thousands of users who are saving time and eating healthier with MealMateAI
          </Typography>
          <Box sx={{ mt: 4, display: 'flex', justifyContent: 'center' }}>
            {isAuthenticated ? (
              <Button 
                variant="contained" 
                size="large"
                onClick={() => navigate('/create-meal-plan')}
              >
                Create Your Meal Plan
              </Button>
            ) : (
              <Button 
                variant="contained" 
                size="large"
                onClick={() => navigate('/register')}
              >
                Get Started Free
              </Button>
            )}
          </Box>
        </Container>
      </Box>
    </>
  );
};

export default Home;