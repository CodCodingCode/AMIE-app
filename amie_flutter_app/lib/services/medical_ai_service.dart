import 'dart:convert';
import 'package:http/http.dart' as http;

class MedicalAIService {
  // Replace with your actual API endpoint
  final String apiUrl = 'http://localhost:5000/predict';
  
  Future<Map<String, dynamic>> getDiagnosis(String symptoms) async {
    try {
      // For development testing, return mock data
      if (symptoms.contains("test")) {
        return _getMockResponse();
      }
      
      // When ready for actual API integration, use this code
      final response = await http.post(
        Uri.parse(apiUrl),
        headers: <String, String>{
          'Content-Type': 'application/json; charset=UTF-8',
        },
        body: jsonEncode(<String, String>{
          'symptoms': symptoms,
        }),
      );

      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else {
        throw Exception('Failed to load prediction: ${response.statusCode}');
      }
    } catch (e) {
      // During development, return mock data on failure
      print('Error connecting to AI service: $e');
      return _getMockResponse();
    }
  }

  // Mock response for development and testing
  Map<String, dynamic> _getMockResponse() {
    return {
      'diagnosis': 'Hypothyroidism',
      'confidence': 0.89,
      'differential_diagnoses': [
        {
          'condition': 'Anemia',
          'confidence': 0.42
        },
        {
          'condition': 'Depression',
          'confidence': 0.38
        }
      ],
      'recommended_tests': [
        'TSH',
        'Free T4',
        'Complete Blood Count'
      ]
    };
  }
}
