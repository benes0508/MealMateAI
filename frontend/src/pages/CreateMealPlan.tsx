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
} from '@mui/material';
import {
  Send as SendIcon,
  ThumbUp as ThumbUpIcon,
  ThumbDown as ThumbDownIcon,
  RestaurantMenu as RestaurantMenuIcon,
} from '@mui/icons-material';
import { generateRAGMealPlan, modifyRAGMealPlan, finalizeRAGMealPlan, MealPlanResponse } from '../services/mealPlannerService';

const CreateMealPlan = () => {
  const navigate = useNavigate();
  
  // State for the prompt and conversation
  const [prompt, setPrompt] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [currentPlan, setCurrentPlan] = useState<MealPlanResponse | null>(null);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [conversation, setConversation] = useState<Array<{type: 'user' | 'system' | 'plan', content: string, planData?: any}>>([
    {
      type: 'system',
      content: 'Welcome to the meal plan creator! Describe the kind of meal plan you want, and I\'ll create it for you. For example: "I need a 7-day vegetarian meal plan with high protein options" or "Create a family-friendly meal plan for 5 days with kid-friendly dinners."'
    }
  ]);
  
  // State for feedback dialog - REMOVED (no longer needed)
  // const [showFeedbackDialog, setShowFeedbackDialog] = useState<boolean>(false);
  // const [feedback, setFeedback] = useState<string>('');
  
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
        content: 'Creating your meal plan preview...'
      }]);
      
      let result;
      
      if (conversationId) {
        // If we have a conversation ID, this is a modification request
        result = await modifyRAGMealPlan(conversationId, userPrompt);
      } else {
        // First time generation - create new conversation
        result = await generateRAGMealPlan(userPrompt);
        if (result.conversation_id) {
          setConversationId(result.conversation_id);
        }
      }
      
      console.log('=== RAG MEAL PLAN PREVIEW ===');
      console.log('Full API response:', JSON.stringify(result, null, 2));
      console.log('=== END PREVIEW ===');
      
      // Remove the typing indicator
      setConversation(prev => prev.filter(msg => msg.content !== 'Creating your meal plan preview...'));
      
      // Add the result to the conversation with preview data
      setConversation(prev => [...prev, {
        type: 'plan',
        content: `Here's your meal plan preview:\n\n**${result.plan_name || 'Custom Meal Plan'}**\n\n${result.plan_explanation || result.description || 'Your personalized meal plan is ready!'}\n\nIf you like this plan, click the thumbs up to save it to your meal plans. If you'd like changes, click thumbs down or describe what you'd like to adjust.`,
        planData: result
      }]);
      
      // Store the current plan preview (not saved yet)
      setCurrentPlan(result);
      
    } catch (err: any) {
      console.error('Error generating meal plan preview:', err);
      
      // Remove the typing indicator
      setConversation(prev => prev.filter(msg => msg.content !== 'Creating your meal plan preview...'));
      
      // Add error message to conversation
      setConversation(prev => [...prev, {
        type: 'system',
        content: `Sorry, I couldn't create your meal plan preview. ${err.message || 'Please try again with a different description.'}`
      }]);
      
      setError('Failed to generate the meal plan preview. Please try again.');
    } finally {
      setLoading(false);
    }
  };
  
  // Handle acceptance of the meal plan
  const handleAcceptPlan = async () => {
    if (currentPlan && conversationId) {
      try {
        setLoading(true);
        
        // Add confirmation message to conversation
        setConversation(prev => [...prev, {
          type: 'system',
          content: 'Saving your meal plan...'
        }]);
        
        // Finalize the meal plan (actually save it to database)
        const finalizedPlan = await finalizeRAGMealPlan(conversationId);
        
        // Remove the loading message
        setConversation(prev => prev.filter(msg => msg.content !== 'Saving your meal plan...'));
        
        // Add success message
        setConversation(prev => [...prev, {
          type: 'system',
          content: `✅ Great! Your meal plan "${finalizedPlan.plan_name}" has been saved to your meal plans. You can view and manage it in your meal planner.`
        }]);
        
        // Navigate to the meal planner to view the created plan
        navigate(`/meal-planner?plan=${finalizedPlan.id}`);
        
      } catch (error: any) {
        console.error('Error finalizing meal plan:', error);
        
        // Remove the loading message
        setConversation(prev => prev.filter(msg => msg.content !== 'Saving your meal plan...'));
        
        // Add error message
        setConversation(prev => [...prev, {
          type: 'system',
          content: `Sorry, there was an error saving your meal plan. ${error.message || 'Please try again.'}`
        }]);
        
        setError('Failed to save the meal plan. Please try again.');
      } finally {
        setLoading(false);
      }
    }
  };
  
  // Handle rejection of the meal plan
  const handleRejectPlan = () => {
    // Add rejection message directly to the conversation
    setConversation(prev => [...prev, {
      type: 'user',
      content: "👎 I don't like this plan"
    }]);
    
    // Add system response encouraging new input
    setConversation(prev => [...prev, {
      type: 'system',
      content: "I understand this plan doesn't meet your needs. Feel free to describe what you'd like differently, and I'll create a new plan based on your preferences. For example, you could specify different cuisines, dietary requirements, or meal types you prefer."
    }]);
    
    // Clear the current plan and conversation state to start fresh
    setCurrentPlan(null);
    setConversationId(null);
  };
  
  // Handle feedback submission - REMOVED (no longer needed with new direct chat approach)

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
                    
                    {/* Plan Summary */}
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
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

                    {/* Meal Plan Details */}
                    {message.planData.meal_plan?.meal_plan && Array.isArray(message.planData.meal_plan.meal_plan) && message.planData.meal_plan.meal_plan.length > 0 ? (
                      <Box sx={{ bgcolor: 'grey.50', p: 2, borderRadius: 1, maxHeight: 300, overflow: 'auto' }}>
                        <Typography variant="subtitle2" sx={{ mb: 1, color: 'text.secondary' }}>
                          📋 Meal Plan Details:
                        </Typography>
                        {message.planData.meal_plan.meal_plan.map((day: any, dayIndex: number) => (
                          <Box key={dayIndex} sx={{ mb: 2, p: 1.5, bgcolor: 'white', borderRadius: 1, border: '1px solid #e0e0e0' }}>
                            <Typography variant="body2" sx={{ fontWeight: 'bold', color: 'primary.main', mb: 1 }}>
                              📅 Day {day.day}:
                            </Typography>
                            {day.meals && day.meals.length > 0 ? (
                              <Box sx={{ ml: 1 }}>
                                {day.meals.map((meal: any, mealIndex: number) => (
                                  <Box key={mealIndex} sx={{ mb: 1, p: 1, bgcolor: 'grey.50', borderRadius: 0.5 }}>
                                    <Typography variant="body2" sx={{ fontWeight: 'medium' }}>
                                      🍽️ <strong>{meal.meal_type.charAt(0).toUpperCase() + meal.meal_type.slice(1)}:</strong>
                                    </Typography>
                                    <Typography variant="body2" sx={{ ml: 2, color: 'text.secondary' }}>
                                      {meal.recipe_name} (Recipe #{meal.recipe_id})
                                    </Typography>
                                  </Box>
                                ))}
                              </Box>
                            ) : (
                              <Typography variant="body2" sx={{ ml: 2, color: 'text.secondary', fontStyle: 'italic' }}>
                                No meals planned for this day
                              </Typography>
                            )}
                          </Box>
                        ))}
                        
                        {/* Summary Section */}
                        <Box sx={{ mt: 2, p: 1.5, bgcolor: 'primary.light', borderRadius: 1, color: 'primary.contrastText' }}>
                          <Typography variant="subtitle2" sx={{ mb: 1 }}>
                            📊 Plan Summary:
                          </Typography>
                          <Typography variant="body2">
                            • Total Days: {message.planData.days || message.planData.meal_plan.meal_plan.length}
                          </Typography>
                          <Typography variant="body2">
                            • Meals per Day: {message.planData.meals_per_day || 3}
                          </Typography>
                          <Typography variant="body2">
                            • Recipes Found: {message.planData.meal_plan.recipes_found || 'N/A'}
                          </Typography>
                          <Typography variant="body2">
                            • Search Queries: {message.planData.meal_plan.queries_used?.join(', ') || 'N/A'}
                          </Typography>
                        </Box>
                      </Box>
                    ) : (
                      <Box sx={{ bgcolor: 'warning.light', p: 2, borderRadius: 1 }}>
                        <Typography variant="body2" color="warning.dark">
                          ⚠️ No meal plan details available. This might be because no suitable recipes were found.
                        </Typography>
                      </Box>
                    )}
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
    </Container>
  );
};

export default CreateMealPlan;
