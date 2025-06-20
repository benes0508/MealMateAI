import { Container, Typography, Box, Divider, Paper } from '@mui/material';

const Cookies = () => {
  return (
    <Container maxWidth="md" sx={{ py: 8 }}>
      <Paper elevation={0} sx={{ p: { xs: 3, md: 5 } }}>
        <Typography variant="h3" component="h1" gutterBottom>
          Cookie Policy
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
            This Cookie Policy explains how MealMateAI ("we", "us", or "our") uses cookies and similar technologies on our website. This policy provides you with information about how we use cookies, how you can manage your cookie preferences, and how these technologies affect your experience on our website.
          </Typography>
        </Box>
        
        <Box sx={{ mb: 4 }}>
          <Typography variant="h5" gutterBottom>
            2. What Are Cookies?
          </Typography>
          <Typography variant="body1" paragraph>
            Cookies are small text files that are placed on your device (computer, tablet, or mobile) when you visit websites. They are widely used to make websites work more efficiently, provide a better user experience, and give website owners information about how their sites are used.
          </Typography>
          <Typography variant="body1" paragraph>
            Cookies may be either "persistent" cookies or "session" cookies. A persistent cookie will remain on your device for a set period or until you delete it. A session cookie will be deleted when you close your browser.
          </Typography>
        </Box>
        
        <Box sx={{ mb: 4 }}>
          <Typography variant="h5" gutterBottom>
            3. Types of Cookies We Use
          </Typography>
          <Typography variant="body1" paragraph sx={{ fontWeight: 'medium' }}>
            Essential Cookies
          </Typography>
          <Typography variant="body1" paragraph>
            These cookies are necessary for the website to function properly. They enable basic functions like page navigation, secure areas, and remembering your preferences. The website cannot function properly without these cookies.
          </Typography>
          
          <Typography variant="body1" paragraph sx={{ fontWeight: 'medium', mt: 2 }}>
            Performance & Analytics Cookies
          </Typography>
          <Typography variant="body1" paragraph>
            These cookies collect information about how visitors use our website, such as which pages they visit most often and if they receive error messages. This information helps us improve our website's performance and user experience.
          </Typography>
          
          <Typography variant="body1" paragraph sx={{ fontWeight: 'medium', mt: 2 }}>
            Functionality Cookies
          </Typography>
          <Typography variant="body1" paragraph>
            These cookies allow the website to remember choices you make (such as your username, language, or region) and provide enhanced, personalized features. They may also be used to provide services you have requested, like watching videos.
          </Typography>
          
          <Typography variant="body1" paragraph sx={{ fontWeight: 'medium', mt: 2 }}>
            Targeting & Advertising Cookies
          </Typography>
          <Typography variant="body1" paragraph>
            These cookies are used to deliver advertisements that are more relevant to you and your interests. They may also limit the number of times you see an advertisement and help measure the effectiveness of advertising campaigns.
          </Typography>
        </Box>
        
        <Box sx={{ mb: 4 }}>
          <Typography variant="h5" gutterBottom>
            4. Third-Party Cookies
          </Typography>
          <Typography variant="body1" paragraph>
            Some cookies may be set by third-party services that appear on our pages, such as analytics tools or embedded content. We do not control these third-party cookies and recommend checking the privacy policies of these parties for information about their cookies.
          </Typography>
        </Box>
        
        <Box sx={{ mb: 4 }}>
          <Typography variant="h5" gutterBottom>
            5. Managing Your Cookie Preferences
          </Typography>
          <Typography variant="body1" paragraph>
            Most web browsers allow you to control cookies through their settings. You can typically find these settings in the "options" or "preferences" menu of your browser. You can choose to accept or reject all cookies or selectively accept certain types.
          </Typography>
          <Typography variant="body1" paragraph>
            Please note that restricting cookies may impact your experience using our website, and some features may not function properly.
          </Typography>
          <Typography variant="body1" paragraph>
            For more information about managing cookies in specific browsers, please refer to the following links:
          </Typography>
          <Typography component="ul" sx={{ pl: 4 }}>
            <li>
              <Typography variant="body1">
                <a href="https://support.google.com/chrome/answer/95647" target="_blank" rel="noopener noreferrer">Google Chrome</a>
              </Typography>
            </li>
            <li>
              <Typography variant="body1">
                <a href="https://support.mozilla.org/en-US/kb/enhanced-tracking-protection-firefox-desktop" target="_blank" rel="noopener noreferrer">Mozilla Firefox</a>
              </Typography>
            </li>
            <li>
              <Typography variant="body1">
                <a href="https://support.apple.com/guide/safari/manage-cookies-and-website-data-sfri11471/mac" target="_blank" rel="noopener noreferrer">Apple Safari</a>
              </Typography>
            </li>
            <li>
              <Typography variant="body1">
                <a href="https://support.microsoft.com/en-us/windows/microsoft-edge-browsing-data-and-privacy-bb8174ba-9d73-dcf2-9b4a-c582b4e640dd" target="_blank" rel="noopener noreferrer">Microsoft Edge</a>
              </Typography>
            </li>
          </Typography>
        </Box>
        
        <Box sx={{ mb: 4 }}>
          <Typography variant="h5" gutterBottom>
            6. Changes to Our Cookie Policy
          </Typography>
          <Typography variant="body1" paragraph>
            We may update our Cookie Policy from time to time to reflect changes in technology, regulation, or our business practices. Any changes will become effective when we post the revised policy on this page. We encourage you to periodically review this page to stay informed about our use of cookies.
          </Typography>
        </Box>
        
        <Box sx={{ mb: 4 }}>
          <Typography variant="h5" gutterBottom>
            7. Contact Us
          </Typography>
          <Typography variant="body1" paragraph>
            If you have any questions about our use of cookies, please contact us at privacy@mealmateai.com.
          </Typography>
        </Box>
      </Paper>
    </Container>
  );
};

export default Cookies;
