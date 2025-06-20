import React from 'react';
import { Container, Typography, Box, Divider, Paper } from '@mui/material';

const Terms = () => {
  return (
    <Container maxWidth="md" sx={{ py: 8 }}>
      <Paper elevation={0} sx={{ p: { xs: 3, md: 5 } }}>
        <Typography variant="h3" component="h1" gutterBottom>
          Terms of Service
        </Typography>
        
        <Typography variant="subtitle1" color="text.secondary" paragraph>
          Last Updated: June 20, 2025
        </Typography>
        
        <Divider sx={{ my: 4 }} />
        
        <Box sx={{ mb: 4 }}>
          <Typography variant="h5" gutterBottom>
            1. Introduction
          </Typography>
          <Typography variant="body1" paragraph>
            Welcome to MealMateAI. These Terms of Service govern your use of our website and services offered by MealMateAI.
            By accessing our website or using our services, you agree to these Terms. Please read them carefully.
          </Typography>
        </Box>
        
        <Box sx={{ mb: 4 }}>
          <Typography variant="h5" gutterBottom>
            2. Definitions
          </Typography>
          <Typography variant="body1" paragraph>
            "Service" refers to the MealMateAI application, website, and any related services.
            "User" refers to individuals who register to use our Service.
            "Content" includes text, images, audio, video, or other material that users submit to our Service.
          </Typography>
        </Box>
        
        <Box sx={{ mb: 4 }}>
          <Typography variant="h5" gutterBottom>
            3. Account Registration
          </Typography>
          <Typography variant="body1" paragraph>
            To use certain features of our Service, you must register for an account. You agree to provide accurate information during registration and to keep your information updated. You are responsible for maintaining the confidentiality of your account and password.
          </Typography>
        </Box>
        
        <Box sx={{ mb: 4 }}>
          <Typography variant="h5" gutterBottom>
            4. User Content
          </Typography>
          <Typography variant="body1" paragraph>
            Users may post content, including recipes, dietary preferences, and comments. By submitting content, you grant MealMateAI a worldwide, non-exclusive license to use, reproduce, and display your content in connection with the Service.
          </Typography>
        </Box>
        
        <Box sx={{ mb: 4 }}>
          <Typography variant="h5" gutterBottom>
            5. Acceptable Use
          </Typography>
          <Typography variant="body1" paragraph>
            You agree not to use our Service to:
          </Typography>
          <Typography component="ul" sx={{ pl: 4 }}>
            <li>
              <Typography variant="body1">Post harmful or illegal content</Typography>
            </li>
            <li>
              <Typography variant="body1">Harass, intimidate, or threaten others</Typography>
            </li>
            <li>
              <Typography variant="body1">Attempt to gain unauthorized access to our systems</Typography>
            </li>
            <li>
              <Typography variant="body1">Impersonate others or misrepresent your affiliation</Typography>
            </li>
          </Typography>
        </Box>
        
        <Box sx={{ mb: 4 }}>
          <Typography variant="h5" gutterBottom>
            6. Intellectual Property
          </Typography>
          <Typography variant="body1" paragraph>
            MealMateAI and its content, features, and functionality are owned by MealMateAI and are protected by copyright, trademark, and other intellectual property laws.
          </Typography>
        </Box>
        
        <Box sx={{ mb: 4 }}>
          <Typography variant="h5" gutterBottom>
            7. Termination
          </Typography>
          <Typography variant="body1" paragraph>
            We may terminate or suspend your account at our sole discretion, without notice, for conduct that we believe violates these Terms or is harmful to other users or us.
          </Typography>
        </Box>
        
        <Box sx={{ mb: 4 }}>
          <Typography variant="h5" gutterBottom>
            8. Limitation of Liability
          </Typography>
          <Typography variant="body1" paragraph>
            MealMateAI shall not be liable for any indirect, incidental, special, consequential, or punitive damages resulting from your use of or inability to use our Service.
          </Typography>
        </Box>
        
        <Box sx={{ mb: 4 }}>
          <Typography variant="h5" gutterBottom>
            9. Changes to Terms
          </Typography>
          <Typography variant="body1" paragraph>
            We may update these Terms from time to time. We will notify you of any changes by posting the new Terms on this page and updating the "Last Updated" date.
          </Typography>
        </Box>
        
        <Box sx={{ mb: 4 }}>
          <Typography variant="h5" gutterBottom>
            10. Governing Law
          </Typography>
          <Typography variant="body1" paragraph>
            These Terms shall be governed by the laws of the jurisdiction in which MealMateAI operates, without regard to its conflict of law provisions.
          </Typography>
        </Box>
        
        <Box sx={{ mb: 4 }}>
          <Typography variant="h5" gutterBottom>
            11. Contact Us
          </Typography>
          <Typography variant="body1" paragraph>
            If you have any questions about these Terms, please contact us at support@mealmateai.com.
          </Typography>
        </Box>
      </Paper>
    </Container>
  );
};

export default Terms;
