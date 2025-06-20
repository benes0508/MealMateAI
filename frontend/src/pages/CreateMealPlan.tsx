import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Container,
  Typography,
  Box,
  TextField,
  Button,
  Paper,
  CircularProgress,
  Alert,
  Card,
  CardContent,
  Divider,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
} from '@mui/material';
import {
  Send as SendIcon,
  ThumbUp as ThumbUpIcon,
  ThumbDown as ThumbDownIcon,
  RestaurantMenu as RestaurantMenuIcon,
  Close as CloseIcon,
} from '@mui/icons-material';
import { generateMealPlanFromText, MealPlanResponse } from '../services/mealPlannerService';

const CreateMealPlan = () => {
  const navigate = useNavigate();
  
  // State for the prompt and conversation
  const [prompt, setPrompt] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [currentPlan, setCurrentPlan] = useState<MealPlanResponse | null>(null);
  const [conversation, setConversation] = useState<Array<{type: 'user' | 'system' | 'plan', content: string, planData?: any}>>([
    {
      type: 'system',
      content: 'Welcome to the meal plan creator! Describe the kind of meal plan you want, and I\'ll create it for you. For example: "I need a 7-day vegetarian meal plan with high protein options" or "Create a family-friendly meal plan for 5 days with kid-friendly dinners."'
    }
  ]);
  
  // State for feedback dialog
  const [showFeedbackDialog, setShowFeedbackDialog] = useState<boolean>(false);
  const [feedback, setFeedback] = useState<string>('');
  
  // Handle sending the prompt
  const handleSendPrompt = async () => {
    if (!prompt.trim()) return;
    
    // Add user message to conversation
    setConversation(prev => [...prev, {
      type: 'user',
      content: prompt
    }]);
    
    // Clear prompt and set loading
    const userPrompt = prompt;
    setPrompt('');
    setLoading(true);
    setError(null);
    
    try {
      // Show typing indicator
      setConversation(prev => [...prev, {
        type: 'system',
        content: 'Generating your meal plan...'
      }]);
      
      // Call the API to generate the meal plan
      const result = await generateMealPlanFromText(userPrompt);
      
      // Remove the typing indicator
      setConversation(prev => prev.filter(msg => msg.content !== 'Generating your meal plan...'));
      
      // Add the result to the conversation
      setConversation(prev => [...prev, {
        type: 'plan',
        content: `I've created a ${result.days}-day meal plan based on your request: "${result.plan_name}".\n\n${result.plan_explanation}`,
        planData: result
      }]);
      
      // Store the current plan
      setCurrentPlan(result);
      
    } catch (err: any) {
      console.error('Error generating meal plan:', err);
      
      // Remove the typing indicator
      setConversation(prev => prev.filter(msg => msg.content !== 'Generating your meal plan...'));
      
      // Add error message to conversation
      setConversation(prev => [...prev, {
        type: 'system',
        content: `Sorry, I couldn't create your meal plan. ${err.message || 'Please try again with a different description.'}`
      }]);
      
      setError('Failed to generate the meal plan. Please try again.');
    } finally {
      setLoading(false);
    }
  };
  
  // Handle acceptance of the meal plan
  const handleAcceptPlan = () => {
    if (currentPlan) {
      navigate(`/meal-planner?plan=${currentPlan.id}`);
    }
  };
  
  // Handle rejection of the meal plan
  const handleRejectPlan = () => {
    setShowFeedbackDialog(true);
  };
  
  // Handle feedback submission
  const handleSubmitFeedback = () => {
    // Add the feedback to the conversation
    if (feedback.trim()) {
      setConversation(prev => [...prev, {
        type: 'user',
        content: `I'd like to make some changes: ${feedback}`
      }]);
    } else {
      setConversation(prev => [...prev, {
        type: 'user',
        content: "I'd like to try a different plan."
      }]);
    }
    
    // Close the dialog and clear feedback
    setShowFeedbackDialog(false);
    setFeedback('');
    setCurrentPlan(null);
    
    // Add system response
    setConversation(prev => [...prev, {
      type: 'system',
      content: 'I understand. Please provide a new description for your meal plan, and I\'ll create a different one for you.'
    }]);
  };

  return (
    <Container maxWidth="md" sx={{ py: 4 }}>
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          Create Your Meal Plan
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Describe what you want in your meal plan, and our AI will create it for you.
        </Typography>
      </Box>

      {/* Conversation area */}
      <Paper 
        elevation={2} 
        sx={{ 
          height: '60vh', 
          mb: 2, 
          p: 2, 
          overflow: 'auto',
          display: 'flex',
          flexDirection: 'column',
          gap: 2,
          bgcolor: 'grey.50'
        }}
      >
        {conversation.map((message, index) => (
          <Box
            key={index}
            sx={{
              alignSelf: message.type === 'user' ? 'flex-end' : 'flex-start',
              maxWidth: '80%'
            }}
          >
            <Card 
              variant="outlined"
              sx={{ 
                bgcolor: message.type === 'user' ? 'primary.light' : 'white',
                color: message.type === 'user' ? 'white' : 'text.primary',
              }}
            >
              <CardContent sx={{ py: 1, px: 2, '&:last-child': { pb: 1 } }}>
                <Typography variant="body1">
                  {message.content}
                </Typography>
                
                {message.type === 'plan' && message.planData && (
                  <Box sx={{ mt: 2 }}>
                    <Divider sx={{ my: 1 }} />
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <Typography variant="subtitle2">
                        {message.planData.days}-Day Meal Plan: {message.planData.plan_name}
                      </Typography>
                      <Box>
                        <IconButton 
                          size="small" 
                          color="success" 
                          onClick={handleAcceptPlan} 
                          title="Accept this plan"
                        >
                          <ThumbUpIcon />
                        </IconButton>
                        <IconButton 
                          size="small" 
                          color="error" 
                          onClick={handleRejectPlan} 
                          title="Reject this plan"
                        >
                          <ThumbDownIcon />
                        </IconButton>
                      </Box>
                    </Box>
                  </Box>
                )}
              </CardContent>
            </Card>
          </Box>
        ))}
      </Paper>

      {/* Input area */}
      <Box sx={{ display: 'flex', gap: 1 }}>
        <TextField
          fullWidth
          variant="outlined"
          placeholder="Describe your ideal meal plan..."
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          disabled={loading}
          onKeyPress={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              handleSendPrompt();
            }
          }}
          multiline
          rows={2}
        />
        <Button
          variant="contained"
          color="primary"
          disabled={loading || !prompt.trim()}
          onClick={handleSendPrompt}
          sx={{ minWidth: '120px' }}
        >
          {loading ? <CircularProgress size={24} /> : (
            <>
              Send <SendIcon sx={{ ml: 1 }} />
            </>
          )}
        </Button>
      </Box>
      
      {error && (
        <Alert severity="error" sx={{ mt: 2 }}>
          {error}
        </Alert>
      )}

      {/* Feedback dialog */}
      <Dialog open={showFeedbackDialog} onClose={() => setShowFeedbackDialog(false)}>
        <DialogTitle>
          What would you like to change?
          <IconButton
            aria-label="close"
            onClick={() => setShowFeedbackDialog(false)}
            sx={{
              position: 'absolute',
              right: 8,
              top: 8,
            }}
          >
            <CloseIcon />
          </IconButton>
        </DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            margin="dense"
            id="feedback"
            label="Your feedback"
            fullWidth
            variant="outlined"
            multiline
            rows={4}
            placeholder="For example: 'I'd like more vegan options' or 'I need higher protein meals'"
            value={feedback}
            onChange={(e) => setFeedback(e.target.value)}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowFeedbackDialog(false)} color="primary">
            Cancel
          </Button>
          <Button onClick={handleSubmitFeedback} color="primary" variant="contained">
            Submit Feedback
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default CreateMealPlan;
