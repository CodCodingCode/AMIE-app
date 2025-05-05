import 'dart:convert';
import 'package:http/http.dart' as http;

class MLService {
  // Replace with your API endpoint when you deploy your model
  final String apiUrl = 'http://localhost:5000/predict';

  Future<String> getPrediction(String symptoms) async {
    try {
      // For now, this is a placeholder
      // When your API is ready, uncomment the code below

      /*
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
        final Map<String, dynamic> data = jsonDecode(response.body);
        return data['diagnosis'] as String;
      } else {
        throw Exception('Failed to load prediction: ${response.statusCode}');
      }
      */

      // Mock response for now
      await Future.delayed(const Duration(seconds: 2));
      return "Based on the symptoms, potential diagnosis: Hypothyroidism";
    } catch (e) {
      throw Exception('Error connecting to ML service: $e');
    }
  }
}
