# role_responder.py
"""
Core RoleResponder class for handling AI agent interactions with proper formatting.
"""

from openai import OpenAI


class RoleResponder:
    """Handles role-based AI interactions with enforced THINKING/ANSWER format"""
    
    def __init__(self, role_instruction, client, model):
        self.client = client
        self.model = model
        self.role_instruction = (
            role_instruction
            + """
        
        CRITICAL FORMAT REQUIREMENT: You MUST always respond in this format:
        
        THINKING: [your reasoning]
        ANSWER: [your actual response]
        
        Start every response with "THINKING:" - this is non-negotiable.
        """
        )

    def ask(self, user_input, max_retries=3):
        """Ask with guaranteed THINKING/ANSWER format and return both raw and clean outputs"""

        for attempt in range(max_retries):
            messages = [
                {"role": "system", "content": self.role_instruction},
                {"role": "user", "content": user_input},
            ]

            response = self.client.chat.completions.create(model=self.model, messages=messages)
            raw_response = response.choices[0].message.content.strip()

            # 🔍 DEBUG: Print the raw GPT response
            print(f"\n🤖 RAW GPT RESPONSE (attempt {attempt + 1}):")
            print("=" * 50)
            print(raw_response)
            print("=" * 50)

            # Clean and normalize the response
            cleaned_response = self.clean_thinking_answer_format(raw_response)

            # 🔍 DEBUG: Print the cleaned response
            print(f"\n🧹 CLEANED RESPONSE:")
            print("=" * 30)
            print(cleaned_response)
            print("=" * 30)

            # Validate the cleaned response
            if self.validate_thinking_answer_format(cleaned_response):
                # Extract just the ANSWER portion for the clean output
                answer_only = self.extract_answer_only(cleaned_response)

                # 🔍 DEBUG: Print the extracted answer
                print(f"\n✅ EXTRACTED ANSWER:")
                print("=" * 20)
                print(answer_only)
                print("=" * 20)

                return {
                    "raw": cleaned_response,  # Full THINKING: + ANSWER:
                    "clean": answer_only,  # Just the answer content
                }
            else:
                # 🔍 DEBUG: Print validation failure
                print(f"\n❌ VALIDATION FAILED for attempt {attempt + 1}")
                print(f"Cleaned response: {cleaned_response[:200]}...")

        # Final fallback
        fallback_raw = f"THINKING: Format enforcement failed after {max_retries} attempts\nANSWER: Unable to get properly formatted response."
        fallback_clean = "Unable to get properly formatted response."

        # 🔍 DEBUG: Print fallback
        print(f"\n💥 FALLBACK TRIGGERED after {max_retries} attempts")
        print(f"Final raw response was: {raw_response[:200]}...")

        return {"raw": fallback_raw, "clean": fallback_clean}

    def extract_answer_only(self, text):
        """Extract just the content after ANSWER:"""
        if "ANSWER:" in text:
            extracted = text.split("ANSWER:", 1)[1].strip()
            # 🔍 DEBUG: Print extraction process
            print(f"\n🎯 EXTRACTING ANSWER from: {text[:100]}...")
            print(f"🎯 EXTRACTED: {extracted[:100]}...")
            return extracted

        # 🔍 DEBUG: No ANSWER found
        print(f"\n⚠️ NO 'ANSWER:' found in text: {text[:100]}...")
        return text.strip()

    def clean_thinking_answer_format(self, text):
        """Clean and ensure exactly one THINKING and one ANSWER section"""

        # 🔍 DEBUG: Print input to cleaning function
        print(f"\n🧼 CLEANING INPUT:")
        print(f"Input length: {len(text)} characters")
        print(f"First 200 chars: {text[:200]}...")
        print(f"Contains THINKING: {'THINKING:' in text}")
        print(f"Contains ANSWER: {'ANSWER:' in text}")

        # Remove any leading/trailing whitespace
        text = text.strip()

        # Find all THINKING and ANSWER positions
        thinking_positions = []
        answer_positions = []

        lines = text.split("\n")
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            if line_stripped.startswith("THINKING:"):
                thinking_positions.append(i)
                print(f"🧠 Found THINKING at line {i}: {line_stripped[:50]}...")
            elif line_stripped.startswith("ANSWER:"):
                answer_positions.append(i)
                print(f"💬 Found ANSWER at line {i}: {line_stripped[:50]}...")

        print(f"📊 THINKING positions: {thinking_positions}")
        print(f"📊 ANSWER positions: {answer_positions}")

        # If we have exactly one of each, check if they're in the right order
        if len(thinking_positions) == 1 and len(answer_positions) == 1:
            thinking_idx = thinking_positions[0]
            answer_idx = answer_positions[0]

            if thinking_idx < answer_idx:
                print(f"✅ Perfect format detected!")
                # Perfect format, just clean up the content
                thinking_content = lines[thinking_idx][9:].strip()  # Remove "THINKING:"
                answer_content = []

                # Collect thinking content (everything between THINKING and ANSWER)
                for i in range(thinking_idx + 1, answer_idx):
                    thinking_content += " " + lines[i].strip()

                # Collect answer content (everything after ANSWER)
                answer_content = lines[answer_idx][7:].strip()  # Remove "ANSWER:"
                for i in range(answer_idx + 1, len(lines)):
                    answer_content += " " + lines[i].strip()

                result = f"THINKING: {thinking_content.strip()}\nANSWER: {answer_content.strip()}"
                print(f"✅ Perfect format result: {result[:100]}...")
                return result

        print(f"⚠️ Format needs fixing...")

        # If format is messed up, try to extract and rebuild
        # Look for the first THINKING and first ANSWER after it
        thinking_content = ""
        answer_content = ""

        first_thinking = -1
        first_answer_after_thinking = -1

        for i, line in enumerate(lines):
            line_stripped = line.strip()
            if line_stripped.startswith("THINKING:") and first_thinking == -1:
                first_thinking = i
                thinking_content = line_stripped[9:].strip()
                print(f"🎯 Using THINKING from line {i}")
            elif (
                line_stripped.startswith("ANSWER:")
                and first_thinking != -1
                and first_answer_after_thinking == -1
            ):
                first_answer_after_thinking = i
                answer_content = line_stripped[7:].strip()
                print(f"🎯 Using ANSWER from line {i}")
                break
            elif first_thinking != -1 and first_answer_after_thinking == -1:
                # Still collecting thinking content
                thinking_content += " " + line_stripped

        # Collect remaining answer content
        if first_answer_after_thinking != -1:
            for i in range(first_answer_after_thinking + 1, len(lines)):
                line_stripped = lines[i].strip()
                # Stop if we hit another THINKING or ANSWER
                if line_stripped.startswith("THINKING:") or line_stripped.startswith(
                    "ANSWER:"
                ):
                    break
                answer_content += " " + line_stripped

        print(f"🔧 Extracted thinking: {thinking_content[:50]}...")
        print(f"🔧 Extracted answer: {answer_content[:50]}...")

        # If we still don't have both parts, try to extract from the raw text
        if not thinking_content or not answer_content:
            print(f"🆘 Last resort extraction...")
            # Last resort: split on the patterns
            if "THINKING:" in text and "ANSWER:" in text:
                parts = text.split("ANSWER:", 1)
                if len(parts) == 2:
                    thinking_part = parts[0]
                    answer_part = parts[1]

                    # Extract thinking content
                    if "THINKING:" in thinking_part:
                        thinking_content = thinking_part.split("THINKING:", 1)[
                            1
                        ].strip()

                    # Clean answer content (remove any nested THINKING/ANSWER)
                    answer_lines = answer_part.split("\n")
                    clean_answer_lines = []
                    for line in answer_lines:
                        if not line.strip().startswith(
                            "THINKING:"
                        ) and not line.strip().startswith("ANSWER:"):
                            clean_answer_lines.append(line)
                    answer_content = " ".join(clean_answer_lines).strip()

        # Fallback if we still don't have proper content
        if not thinking_content:
            print(f"❌ Failed to extract thinking content")
            thinking_content = "Unable to extract thinking content properly"
        if not answer_content:
            print(f"❌ Failed to extract answer content")
            answer_content = "Unable to extract answer content properly"

        final_result = (
            f"THINKING: {thinking_content.strip()}\nANSWER: {answer_content.strip()}"
        )
        print(f"🏁 Final cleaned result: {final_result[:100]}...")
        return final_result

    def validate_thinking_answer_format(self, text):
        """Validate that the text has exactly one THINKING and one ANSWER in correct order"""
        lines = text.split("\n")

        thinking_count = 0
        answer_count = 0
        thinking_first = False

        for line in lines:
            line_stripped = line.strip()
            if line_stripped.startswith("THINKING:"):
                thinking_count += 1
                if answer_count == 0:  # No ANSWER seen yet
                    thinking_first = True
            elif line_stripped.startswith("ANSWER:"):
                answer_count += 1

        is_valid = thinking_count == 1 and answer_count == 1 and thinking_first
        print(
            f"✅ VALIDATION: thinking_count={thinking_count}, answer_count={answer_count}, thinking_first={thinking_first}, valid={is_valid}"
        )

        return is_valid