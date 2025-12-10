Privacy Policy – LeetCode Solution Assistant
============================================

Last updated: 2024-11-24

1) What this extension does  
- Provides step-by-step explanations and code suggestions for LeetCode problems in a side panel.  
- Sends your messages and the current problem context to our backend to generate replies.

2) Data we collect  
- Chat content you type in the extension.  
- LeetCode problem identifiers captured from the page (e.g., title/number).  
- Basic session metadata: random session ID and auth token to keep conversation state.  
- Minimal device/browser info sent with API requests (IP, user agent) for security and rate limiting.  
- We do not collect passwords, payment info, or unrelated browsing history.

3) How we use the data  
- To generate responses and maintain conversation context.  
- To improve reliability (debugging errors, preventing abuse).  
- Aggregated, de-identified analytics to understand feature usage (no personal chat content is sold or shared for ads).

4) Data storage and retention  
- Session data and chat history are stored on our backend to provide replies.  
- We retain session data only as long as needed for active use, then delete or anonymize it.  
- You can request deletion at any time (see “Your choices”).

5) Permissions and why  
- `sidePanel`: show the assistant UI alongside LeetCode.  
- `activeTab` / `tabs`: read the active tab URL/title to link the chat to the open LeetCode problem.  
- `scripting` + host permission `https://leetcode.com/*`: inject a content script on LeetCode pages to read the problem title/number or selected text when you ask.  
- `storage`: save lightweight settings (e.g., preferred language, session/auth tokens) locally.  
We do not use these permissions to access unrelated sites or data.

6) Remote services  
- The extension calls our backend at [your API host] to process prompts via an LLM provider.  
- Chat content and LeetCode context are sent to this service to generate responses.

7) Sharing  
- We do not sell your data.  
- We may share data with service providers (e.g., cloud hosting, LLM API) solely to operate the assistant, under confidentiality and data-protection terms.  
- We may disclose data if required by law or to protect our users and service.

8) Cookies/local storage  
- We use cookies or local storage to keep your session authenticated and remember preferences.  
- These are limited to the extension’s function and are not used for advertising.

9) Security  
- Data in transit is protected with HTTPS.  
- Access to backend data is restricted to authorized personnel and services.  
- No method is 100% secure; we work to keep protections current.

10) Your choices  
- Clear extension data via your browser or request deletion of backend session data by contacting us at [contact email].  
- Uninstalling the extension stops data collection.  
- Please avoid sharing sensitive personal information in chat messages.

11) Children’s privacy  
- Not intended for children under 13. We do not knowingly collect data from children.

12) Changes to this policy  
- We may update this policy and will adjust the “Last updated” date. Material changes will be communicated via release notes or the listing.

13) Contact  
- Questions or deletion requests: siddharthumachandarusa@gmail.com.
