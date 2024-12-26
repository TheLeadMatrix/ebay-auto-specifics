chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.imageUrl) {
    // Replace with your Replit URL after deploying
    const REPLIT_URL = "https://510433b1-8c7b-4142-aa4f-668fb05f1778-00-tlvik6nxn9ic.riker.replit.dev/";
    
    fetch(REPLIT_URL, {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({ imageUrl: message.imageUrl })
    })
    .then(res => res.json())
    .then(data => {
      console.log("Item Specifics received:", data.itemSpecifics);
      chrome.tabs.sendMessage(sender.tab.id, {
        type: "SPECIFICS_RESULT",
        data: data.itemSpecifics
      });
    })
    .catch(err => console.error("Error:", err));
  }
}); 