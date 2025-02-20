import React, { useState } from "react";
import { View, TextInput, Button, Text, ScrollView, StyleSheet } from "react-native";

const ChatScreen = () => {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [isVisible, setIsVisible] = useState(false);
  const askAI = async () => {
    try {
      const response = await fetch(`http://127.0.0.1:8000/ask?question=${question}`);
      const data = await response.json();
      setAnswer(data.answer);
      setQuestion("");
      setIsVisible(true);
      setSearchResults([]); // ✅ Clear search results on new question
    } catch (error) {
      console.error("Error fetching AI response:", error);
    }
  };

  const searchAI = async () => {
    try {
      const response = await fetch(`http://127.0.0.1:8000/search?query=${question}`);
      const data = await response.json();
      setSearchResults(Array.isArray(data.matches) ? data.matches : []); // ✅ Always ensures an array
      console.log("Search results:", searchResults);
    } catch (error) {
      console.error("Error fetching past matches:", error);
      setSearchResults([]); // ✅ Set empty array on error
    }
  };

  return (
    <View style={{ flex: 1, padding: 100 }}>
      <TextInput
        value={question}
        onChangeText={setQuestion}
        placeholder="Ask a question..."
        style={{
          borderWidth: 1,
          borderColor: "#ccc",
          padding: 10,
          borderRadius: 8,
          marginBottom: 10,
        }}
      />
      <Button title="Ask" onPress={askAI} />
      <Button title="Search History" onPress={searchAI} color="gray" />
      <ScrollView>
        {answer ? <Text style={{ marginTop: 20 }}>Answer: {answer}</Text> : null}
        {isVisible && <Button title="Clear" onPress={() => { setAnswer(""); setIsVisible(false); }} />} 
      </ScrollView>
      <ScrollView style={{ marginTop: 20 }}>
        {searchResults.length > 0 && <Text>Past Matches:</Text>}
        {searchResults.map((result, index) => (
          <Text key={index} style={{ padding: 5, backgroundColor: "#f5f5f5", marginTop: 5 }}>
            {result}
          </Text>
        ))}
      </ScrollView>
    </View>
  );
};

export default ChatScreen;



const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 16,
  },
  titleContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  stepContainer: {
    gap: 8,
    marginBottom: 8,
  },
  reactLogo: {
    height: 178,
    width: 290,
    bottom: 0,
    left: 0,
    position: 'absolute',
  },
});
