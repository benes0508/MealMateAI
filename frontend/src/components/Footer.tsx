import { Box, Container, Typography, Link, Grid, IconButton } from '@mui/material';
import { Facebook, Twitter, Instagram, LinkedIn } from '@mui/icons-material';
import { Link as RouterLink } from 'react-router-dom';

const Footer = () => {
  return (
    <Box component="footer" sx={{ py: 5, bgcolor: 'background.paper', mt: 'auto' }}>
      <Container maxWidth="lg">
        <Grid container spacing={4}>
          <Grid item xs={12} sm={4}>
            <Typography variant="h6" color="primary" gutterBottom>
              MealMateAI
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Your personal AI-powered meal planning assistant.
              Making healthy eating simple and personalized.
            </Typography>
            <Box sx={{ mt: 2 }}>
              <IconButton color="primary" aria-label="Facebook" component="a" href="https://facebook.com" target="_blank">
                <Facebook />
              </IconButton>
              <IconButton color="primary" aria-label="Twitter" component="a" href="https://twitter.com" target="_blank">
                <Twitter />
              </IconButton>
              <IconButton color="primary" aria-label="Instagram" component="a" href="https://instagram.com" target="_blank">
                <Instagram />
              </IconButton>
              <IconButton color="primary" aria-label="LinkedIn" component="a" href="https://linkedin.com" target="_blank">
                <LinkedIn />
              </IconButton>
            </Box>
          </Grid>
          <Grid item xs={12} sm={4}>
            <Typography variant="h6" color="text.primary" gutterBottom>
              Quick Links
            </Typography>
            <Box>
              <Link component={RouterLink} to="/" color="inherit" display="block" sx={{ mb: 1 }}>
                Home
              </Link>
              <Link component={RouterLink} to="/recipes" color="inherit" display="block" sx={{ mb: 1 }}>
                Recipes
              </Link>
              <Link component={RouterLink} to="/meal-planner" color="inherit" display="block" sx={{ mb: 1 }}>
                Meal Planner
              </Link>
            </Box>
          </Grid>
          <Grid item xs={12} sm={4}>
            <Typography variant="h6" color="text.primary" gutterBottom>
              Legal
            </Typography>
            <Box>
              <Link component={RouterLink} to="/terms" color="inherit" display="block" sx={{ mb: 1 }}>
                Terms of Service
              </Link>
              <Link component={RouterLink} to="/privacy" color="inherit" display="block" sx={{ mb: 1 }}>
                Privacy Policy
              </Link>
              <Link component={RouterLink} to="/cookies" color="inherit" display="block" sx={{ mb: 1 }}>
                Cookie Policy
              </Link>
            </Box>
          </Grid>
        </Grid>
        <Box sx={{ mt: 3, borderTop: 1, borderColor: 'divider', pt: 3, textAlign: 'center' }}>
          <Typography variant="body2" color="text.secondary">
            © {new Date().getFullYear()} MealMateAI. All rights reserved.
          </Typography>
        </Box>
      </Container>
    </Box>
  );
};

export default Footer;