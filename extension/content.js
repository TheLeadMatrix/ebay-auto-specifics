// Function to find the main product image
function findProductImage() {
  const imgElement = document.querySelector(".img-tag-wrapper img");
  if (imgElement) {
    const imageUrl = imgElement.src;
    chrome.runtime.sendMessage({ imageUrl: imageUrl });
  }
}

// Run when page loads
document.addEventListener('DOMContentLoaded', findProductImage);

// Listen for results from background script
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === "SPECIFICS_RESULT") {
    console.log("Received specifics:", message.data);
    // TODO: Add code to populate eBay fields with the received data
  }
}); 