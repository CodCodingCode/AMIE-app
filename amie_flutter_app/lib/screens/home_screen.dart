import 'package:flutter/material.dart';
import '../services/medical_ai_service.dart';

class ChatMessage {
  final String text;
  final bool isUser;

  ChatMessage({required this.text, required this.isUser});
}

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  HomeScreenState createState() => HomeScreenState();
}

class HomeScreenState extends State<HomeScreen> {
  final TextEditingController _messageController = TextEditingController();
  final ScrollController _scrollController = ScrollController();
  final List<ChatMessage> _messages = [];
  bool _isTyping = false;
  int _conversationTurns = 0;
  static const int _maxTurns = 5; // Maximum turns before diagnosis
  
  @override
  void initState() {
    super.initState();
    // Add initial greeting message
    _addBotMessage("Hello! I'm AMIE, your medical assistant. What do you need help with medically today?");
  }

  @override
  void dispose() {
    _messageController.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  void _addBotMessage(String message) {
    setState(() {
      _messages.add(ChatMessage(text: message, isUser: false));
      _isTyping = false;
    });
    _scrollToBottom();
  }

  void _addUserMessage(String message) {
    if (message.trim().isEmpty) return;
    
    setState(() {
      _messages.add(ChatMessage(text: message, isUser: true));
      _messageController.clear();
      _isTyping = true;
      _conversationTurns++;
    });
    _scrollToBottom();

    // Simulate AI thinking time
    Future.delayed(const Duration(milliseconds: 500), () => _processMessage(message));
  }

  Future<void> _processMessage(String message) async {
    // Increase the buffer time to give more "thinking" time
    await Future.delayed(const Duration(milliseconds: 1000));
    
    if (_conversationTurns >= _maxTurns) {
      // After max turns, provide diagnosis
      await _provideDiagnosis(message);
    } else {
      // Continue conversation with follow-up questions
      await _askFollowUpQuestion(message);
    }
  }

  Future<void> _askFollowUpQuestion(String message) async {
    try {
      final MedicalAIService aiService = MedicalAIService();
      
      // Get response based on conversation history
      String allConversation = _messages
          .map((msg) => "${msg.isUser ? 'User: ' : 'AI: '}${msg.text}")
          .join("\n");
      
      String response;

      if (_conversationTurns < _maxTurns - 1) {
        // Ask follow-up questions based on symptoms
        if (message.toLowerCase().contains("pain")) {
          response = "Can you describe the pain? Is it sharp, dull, or throbbing?";
        } else if (message.toLowerCase().contains("fever")) {
          response = "How high is your temperature and when did the fever start?";
        } else if (message.toLowerCase().contains("rash")) {
          response = "Where is the rash located and does it itch?";
        } else if (_conversationTurns == 1) {
          response = "How long have you been experiencing these symptoms?";
        } else if (_conversationTurns == 2) {
          response = "What is your age and sex?";
        } else if (_conversationTurns == 3) {
          response = "Do you have any known medical conditions or allergies?";
        } else if (_conversationTurns == 4) {
          response = "Are you currently taking any medications?";
        } else if (_conversationTurns % 3 == 0) {
          response = "Have your symptoms changed since they first appeared?";
        } else {
          // Get random follow-up questions if no specific condition is detected
          final questions = [
            "Have you experienced these symptoms before?",
            "Is there anything that makes the symptoms better or worse?",
            "Have you tried any treatments or home remedies?",
            "Does anyone in your family have similar symptoms?",
            "Have you traveled anywhere recently?",
            "Have you changed your diet or routine lately?",
            "Are your symptoms worse at any particular time of day?",
            "How are these symptoms affecting your daily activities?",
            "Are you experiencing any stress or changes in your life?",
            "Have you noticed any patterns to when the symptoms occur?"
          ];
          response = questions[_conversationTurns % questions.length];
        }
      } else {
        // Final question before diagnosis
        response = "Thank you for all this information. Let me analyze your symptoms to provide a diagnosis...";
      }

      _addBotMessage(response);
      
      // If it's the last turn, proceed to diagnosis after a short delay
      if (_conversationTurns >= _maxTurns - 1) {
        Future.delayed(const Duration(seconds: 2), () => _provideDiagnosis(allConversation));
      }
      
    } catch (e) {
      _addBotMessage("I'm having trouble processing your information. Could you try rephrasing that?");
    }
  }

  Future<void> _provideDiagnosis(String conversationHistory) async {
    try {
      setState(() {
        _isTyping = true;
      });
      
      final MedicalAIService aiService = MedicalAIService();
      final diagnosis = await aiService.getDiagnosis(conversationHistory);
      
      // Format diagnosis from the medical AI service
      String diagnosisText = "Based on the symptoms, potential diagnosis: ${diagnosis['diagnosis']}";
      
      // Add confidence if available
      if (diagnosis.containsKey('confidence')) {
        diagnosisText += "\n\nConfidence: ${(diagnosis['confidence'] * 100).toInt()}%";
      }
      
      // Add differential diagnoses if available
      if (diagnosis.containsKey('differential_diagnoses')) {
        diagnosisText += "\n\nDifferential diagnoses:";
        for (var diff in diagnosis['differential_diagnoses']) {
          diagnosisText += "\n- ${diff['condition']} (${(diff['confidence'] * 100).toInt()}%)";
        }
      }
      
      // Add recommended tests if available
      if (diagnosis.containsKey('recommended_tests')) {
        diagnosisText += "\n\nRecommended tests:";
        for (var test in diagnosis['recommended_tests']) {
          diagnosisText += "\n- $test";
        }
      }
      
      diagnosisText += "\n\nThis is for informational purposes only. Please consult a healthcare professional.";
      
      _addBotMessage(diagnosisText);
      
    } catch (e) {
      _addBotMessage("I'm sorry, I couldn't generate a diagnosis at this time. Please consult a healthcare professional for proper evaluation.");
    }
  }

  void _scrollToBottom() {
    // Scroll to bottom of chat after adding new messages
    Future.delayed(const Duration(milliseconds: 100), () {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOut,
        );
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('AMIE Medical Assistant'),
        elevation: 1,
      ),
      body: Column(
        children: [
          Expanded(
            child: ListView.builder(
              controller: _scrollController,
              padding: const EdgeInsets.all(8.0),
              itemCount: _messages.length,
              itemBuilder: (context, index) {
                final message = _messages[index];
                return _buildMessageBubble(message);
              },
            ),
          ),
          if (_isTyping)
            const Padding(
              padding: EdgeInsets.symmetric(horizontal: 16.0),
              child: Row(
                children: [
                  SizedBox(
                    width: 24,
                    height: 24,
                    child: CircularProgressIndicator(strokeWidth: 2.5),
                  ),
                  SizedBox(width: 8),
                  Text("AMIE is thinking...", style: TextStyle(fontSize: 16)),
                ],
              ),
            ),
          _buildMessageComposer(),
        ],
      ),
    );
  }

  Widget _buildMessageBubble(ChatMessage message) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4.0),
      child: Row(
        mainAxisAlignment: message.isUser 
            ? MainAxisAlignment.end 
            : MainAxisAlignment.start,
        children: [
          if (!message.isUser) 
            const CircleAvatar(
              backgroundColor: Colors.blue,
              child: Text('A', style: TextStyle(color: Colors.white)),
            ),
          const SizedBox(width: 8),
          Flexible(
            child: Container(
              padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 16),
              decoration: BoxDecoration(
                color: message.isUser 
                    ? Colors.blue.shade100 
                    : Colors.grey.shade200,
                borderRadius: BorderRadius.circular(16),
              ),
              child: Text(message.text),
            ),
          ),
          const SizedBox(width: 8),
          if (message.isUser) 
            const CircleAvatar(
              backgroundColor: Colors.green,
              child: Text('U', style: TextStyle(color: Colors.white)),
            ),
        ],
      ),
    );
  }

  Widget _buildMessageComposer() {
    return Container(
      padding: const EdgeInsets.all(8.0),
      decoration: BoxDecoration(
        color: Theme.of(context).cardColor,
        boxShadow: [
          BoxShadow(
            offset: const Offset(0, -2),
            blurRadius: 4,
            color: Colors.black.withOpacity(0.1),
          ),
        ],
      ),
      child: Row(
        children: [
          Expanded(
            child: TextField(
              controller: _messageController,
              decoration: const InputDecoration(
                hintText: "Describe your symptoms...",
                border: OutlineInputBorder(),
                contentPadding: EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                // Removed the suffixIcon with thinking indicator
              ),
              maxLines: null,
              textInputAction: TextInputAction.send,
              onSubmitted: (value) {
                if (!_isTyping) {
                  _addUserMessage(value);
                }
              },
            ),
          ),
          const SizedBox(width: 8),
          FloatingActionButton(
            onPressed: _isTyping 
                ? null 
                : () => _addUserMessage(_messageController.text),
            mini: true,
            child: const Icon(Icons.send),
          ),
        ],
      ),
    );
  }
}
