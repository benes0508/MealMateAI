import { Container, Typography, Box, Divider, Paper } from '@mui/material';

const Privacy = () => {
  return (
    <Container maxWidth="md" sx={{ py: 8 }}>
      <Paper elevation={0} sx={{ p: { xs: 3, md: 5 } }}>
        <Typography variant="h3" component="h1" gutterBottom>
          Privacy Policy
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
            MealMateAI ("we", "our", or "us") is committed to protecting your privacy. This Privacy Policy explains how we collect, use, disclose, and safeguard your information when you use our website and services.
          </Typography>
          <Typography variant="body1" paragraph>
            Please read this Privacy Policy carefully. If you do not agree with the terms of this Privacy Policy, please do not access our services.
          </Typography>
        </Box>
        
        <Box sx={{ mb: 4 }}>
          <Typography variant="h5" gutterBottom>
            2. Information We Collect
          </Typography>
          <Typography variant="body1" paragraph sx={{ fontWeight: 'medium' }}>
            Personal Information
          </Typography>
          <Typography variant="body1" paragraph>
            We may collect personal information that you voluntarily provide when using our service, including:
          </Typography>
          <Typography component="ul" sx={{ pl: 4 }}>
            <li>
              <Typography variant="body1">Name, email address, and other contact information</Typography>
            </li>
            <li>
              <Typography variant="body1">Account credentials (username and password)</Typography>
            </li>
            <li>
              <Typography variant="body1">Dietary preferences and restrictions</Typography>
            </li>
            <li>
              <Typography variant="body1">Health information you choose to share</Typography>
            </li>
            <li>
              <Typography variant="body1">User-generated content such as recipes and meal plans</Typography>
            </li>
          </Typography>
          
          <Typography variant="body1" paragraph sx={{ fontWeight: 'medium', mt: 2 }}>
            Usage Information
          </Typography>
          <Typography variant="body1" paragraph>
            We may automatically collect certain information when you use our service, including:
          </Typography>
          <Typography component="ul" sx={{ pl: 4 }}>
            <li>
              <Typography variant="body1">IP address and device information</Typography>
            </li>
            <li>
              <Typography variant="body1">Browser type and version</Typography>
            </li>
            <li>
              <Typography variant="body1">Pages you visit and features you use</Typography>
            </li>
            <li>
              <Typography variant="body1">Time spent on pages and interaction patterns</Typography>
            </li>
          </Typography>
        </Box>
        
        <Box sx={{ mb: 4 }}>
          <Typography variant="h5" gutterBottom>
            3. How We Use Your Information
          </Typography>
          <Typography variant="body1" paragraph>
            We may use the information we collect for various purposes, including:
          </Typography>
          <Typography component="ul" sx={{ pl: 4 }}>
            <li>
              <Typography variant="body1">Providing, maintaining, and improving our services</Typography>
            </li>
            <li>
              <Typography variant="body1">Personalizing your experience and content</Typography>
            </li>
            <li>
              <Typography variant="body1">Creating and managing your account</Typography>
            </li>
            <li>
              <Typography variant="body1">Communicating with you about updates and promotions</Typography>
            </li>
            <li>
              <Typography variant="body1">Analyzing usage patterns and trends</Typography>
            </li>
            <li>
              <Typography variant="body1">Detecting, preventing, and addressing fraud or security issues</Typography>
            </li>
          </Typography>
        </Box>
        
        <Box sx={{ mb: 4 }}>
          <Typography variant="h5" gutterBottom>
            4. Information Sharing and Disclosure
          </Typography>
          <Typography variant="body1" paragraph>
            We may share your information in the following situations:
          </Typography>
          <Typography component="ul" sx={{ pl: 4 }}>
            <li>
              <Typography variant="body1">With service providers who help us operate our business</Typography>
            </li>
            <li>
              <Typography variant="body1">To comply with legal obligations</Typography>
            </li>
            <li>
              <Typography variant="body1">To protect our rights, privacy, safety, or property</Typography>
            </li>
            <li>
              <Typography variant="body1">In connection with a business transfer or acquisition</Typography>
            </li>
            <li>
              <Typography variant="body1">With your consent or at your direction</Typography>
            </li>
          </Typography>
        </Box>
        
        <Box sx={{ mb: 4 }}>
          <Typography variant="h5" gutterBottom>
            5. Data Security
          </Typography>
          <Typography variant="body1" paragraph>
            We implement appropriate security measures to protect your personal information. However, no method of transmission over the Internet or electronic storage is 100% secure, and we cannot guarantee absolute security.
          </Typography>
        </Box>
        
        <Box sx={{ mb: 4 }}>
          <Typography variant="h5" gutterBottom>
            6. Your Data Protection Rights
          </Typography>
          <Typography variant="body1" paragraph>
            Depending on your location, you may have the following rights:
          </Typography>
          <Typography component="ul" sx={{ pl: 4 }}>
            <li>
              <Typography variant="body1">Access to your personal data</Typography>
            </li>
            <li>
              <Typography variant="body1">Correction of inaccurate data</Typography>
            </li>
            <li>
              <Typography variant="body1">Deletion of your personal data</Typography>
            </li>
            <li>
              <Typography variant="body1">Restriction of processing of your data</Typography>
            </li>
            <li>
              <Typography variant="body1">Data portability</Typography>
            </li>
            <li>
              <Typography variant="body1">Objection to processing of your data</Typography>
            </li>
          </Typography>
        </Box>
        
        <Box sx={{ mb: 4 }}>
          <Typography variant="h5" gutterBottom>
            7. Children's Privacy
          </Typography>
          <Typography variant="body1" paragraph>
            Our services are not intended for children under 13 years of age. We do not knowingly collect personal information from children under 13. If you are a parent or guardian and believe your child has provided us with personal information, please contact us.
          </Typography>
        </Box>
        
        <Box sx={{ mb: 4 }}>
          <Typography variant="h5" gutterBottom>
            8. Changes to This Privacy Policy
          </Typography>
          <Typography variant="body1" paragraph>
            We may update our Privacy Policy from time to time. We will notify you of any changes by posting the new Privacy Policy on this page and updating the "Last Updated" date.
          </Typography>
        </Box>
        
        <Box sx={{ mb: 4 }}>
          <Typography variant="h5" gutterBottom>
            9. Contact Us
          </Typography>
          <Typography variant="body1" paragraph>
            If you have any questions about this Privacy Policy, please contact us at privacy@mealmateai.com.
          </Typography>
        </Box>
      </Paper>
    </Container>
  );
};

export default Privacy;
