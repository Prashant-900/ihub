export const triggers = [
  { name: "madtrigger", description: "Character becomes angry or frustrated." },
  { name: "embarrassedtrigger", description: "Character shows embarrassment or shyness." },
  { name: "headnodtrigger", description: "Character nods head in agreement or acknowledgment." },
  { name: "confusedtrigger", description: "Character looks puzzled or unsure." },
  { name: "disappointedtrigger", description: "Character shows disappointment or sadness." },
  { name: "happytrigger", description: "Character smiles or shows general happiness." },
  { name: "winktrigger", description: "Character performs a playful wink." },
  { name: "happyagreetrigger", description: "Character smiles and nods in cheerful agreement." },
  { name: "lightmadtrigger", description: "Character appears slightly annoyed or irritated." },
  { name: "sadtiredtrigger", description: "Character looks both sad and tired." },
  { name: "sadtrigger", description: "Character shows sadness or sorrow." },
  { name: "happynotrigger", description: "Character smiles while shaking head, suggesting amused disagreement." },
  { name: "bothertrigger", description: "Character appears bothered or uncomfortable." },
  { name: "shaketrigger", description: "Character shakes head in disapproval or disbelief." }
];


export const expressions = [
  { name: "Angry.exp3", description: "Displays an angry expression with narrowed eyes or tense mouth." },
  { name: "f01.exp3", description: "Sad and eyes open" },
  { name: "Normal.exp3", description: "Neutral, default face with no special emotion." },
  { name: "f02.exp3", description: "Sad eyes kinda tired." },
  { name: "Smile.exp3", description: "Cheerful smiling face showing happiness." },
  { name: "Blushing.exp3", description: "Face with blush — shows shyness, affection, or embarrassment." },
  { name: "Surprised.exp3", description: "Eyes widened and mouth open — expresses surprise or shock." },
  { name: "Sad.exp3", description: "Downturned mouth and eyes — conveys sadness or disappointment." }
];
export const expressionMap = {
  "Angry.exp3": 0,
  "f01.exp3": 1,
  "Normal.exp3": 2,
  "f02.exp3": 3,
  "Smile.exp3": 4,
  "Blushing.exp3": 5,
  "Surprised.exp3": 6,
  "Sad.exp3": 7
};

export const backgroundMap = {
    "Zenless Zero" : "bg_1",
    "Rei" : "bg_2",
    "Reze" : "bg_3",
}