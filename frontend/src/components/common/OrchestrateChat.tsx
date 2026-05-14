import { Loading } from "@carbon/react";
import { useEffect, useState } from "react";
import { DARK_MODE_STYLES, STYLE_ELEMENT_ID } from "./OrchestrateChat.styles";

// Extend Window interface for Watson Orchestrate
declare global {
  interface Window {
    wxOConfiguration: any;
    wxoLoader: any;
    __hasLoadedWatsonSources__: boolean;
  }
}

interface OrchestrateChatProps {
  onMessageReceived?: ((message: string) => void) | null;
  sendMessage?: string;
}

const HTML_CONTAINER_ID = "root";

// Cache the style element to avoid recreating it on every call
let cachedStyleElement: HTMLStyleElement | null = null;

export function OrchestrateChat({
  onMessageReceived = null,
  sendMessage = "",
}: OrchestrateChatProps) {
  const [chatInstance, setChatInstance] = useState<any>(null);

  /**
   * Inject dark mode styles after widget loads
   * Uses cached style element for better performance
   */
  const injectDarkModeStyles = () => {
    if (!cachedStyleElement) {
      cachedStyleElement = document.createElement("style");
      cachedStyleElement.id = STYLE_ELEMENT_ID;
      document.head.appendChild(cachedStyleElement);
    }
    cachedStyleElement.textContent = DARK_MODE_STYLES;
  };

  // Register event handlers when chat loads
  const onChatLoad = (instance: any) => {
    setChatInstance(instance);
    injectDarkModeStyles();
    if (window.wxoLoader) {
      window.wxoLoader.chatInstance = instance;
    }

    if (typeof instance.on === "function") {
      // Handler for send events
      instance.on("send", (_event: any) => {
        // console.log("Send event:", _event);
        // TODO: Add custom send handler logic here
        // if (monitoringService && _event.message?.thread_id) {
        //   monitoringService.setThreadId(_event.message.thread_id);
        // }
      });

      // Handler for receive events
      instance.on("receive", (event: any) => {
        // console.log("Receive event:", event);
        // TODO: Add custom receive handler logic here
        
        // Extract message text and pass to parent
        if (onMessageReceived && event.message?.content) {
          const lastItem =
            event.message.content[event.message.content.length - 1];
          if (lastItem?.text) {
            onMessageReceived(lastItem.text);
          }
        }
        // if (monitoringService && event.message?.threadId) {
        //   monitoringService.setThreadId(event.message.threadId);
        // }
      });

      // Handler for pre-receive events
      instance.on("pre:receive", (_event: any) => {
        // console.log("Pre-receive event:", _event);
        // TODO: Add custom pre-receive handler logic here
      });

      // Handler for feedback events
      instance.on("feedback", (_event: any) => {
        // console.log("Feedback event:", _event);
        // TODO: Add custom feedback handler logic here
      });

      // TODO: Add custom language selector if needed
      // instance.updateCustomHeaderItems([getCustomLanguageSelector()]);
    }
  };

  // Load watsonx Orchestrate script
  useEffect(() => {
    // TODO: Replace these with your actual Watson Orchestrate configuration
    const WXO_HOST_URL = import.meta.env.VITE_WXO_HOST_URL || "";
    const WXO_ORCHESTRATION_ID = import.meta.env.VITE_WXO_ORCHESTRATION_ID || "";
    const WXO_AGENT_ID = import.meta.env.VITE_WXO_AGENT_ID || "";
    const WXO_AGENT_ENVIRONMENT_ID = import.meta.env.VITE_WXO_AGENT_ENVIRONMENT_ID || "";

    if (window.__hasLoadedWatsonSources__) {
      // If already loaded, just show the container
      const container = document.getElementById(HTML_CONTAINER_ID);
      if (container) {
        container.style.display = "block";
      }
      return;
    }

    // Validate required environment variables
    if (!WXO_HOST_URL || !WXO_ORCHESTRATION_ID) {
      console.error(
        "Watson Orchestrate configuration error: Missing required environment variables"
      );
      console.error("VITE_WXO_HOST_URL:", WXO_HOST_URL || "NOT SET");
      console.error(
        "VITE_WXO_ORCHESTRATION_ID:",
        WXO_ORCHESTRATION_ID || "NOT SET"
      );
      return;
    }

    window.__hasLoadedWatsonSources__ = true;

    // Construct CRN from orchestration ID
    const constructCRN = (orchestrationID: string, hostURL: string) => {
      const parts = orchestrationID.split("_");
      if (parts.length >= 2) {
        const accountId = parts[0];
        const instanceId = parts[1];
        const regionMatch = hostURL.match(/https:\/\/([^.]+)\./);
        const region = regionMatch ? regionMatch[1] : "eu-de";
        return `crn:v1:bluemix:public:watsonx-orchestrate:${region}:a/${accountId}:${instanceId}::`;
      }
      return null;
    };

    window.wxOConfiguration = {
      orchestrationID: WXO_ORCHESTRATION_ID || null,
      hostURL: WXO_HOST_URL || null,
      rootElementID: HTML_CONTAINER_ID,
      showLauncher: false,
      deploymentPlatform: "ibmcloud",
      crn: constructCRN(WXO_ORCHESTRATION_ID, WXO_HOST_URL),
      chatOptions: {
        onLoad: onChatLoad,
        agentId: WXO_AGENT_ID || null,
        agentEnvironmentId: WXO_AGENT_ENVIRONMENT_ID || null,
        // Disable search docs and voice mode
        enableSearchDocs: false,
        enableVoiceMode: false,
      },
      defaultLocale: "en",

      layout: {
        showHeader: true,
        form: "custom",
        showOrchestrateHeader: true,
        width: "600px",
        height: "600px",
        showMaxWidth: false,
      },

      // Dark mode color scheme
      style: {
        headerColor: "#262626",
        userMessageBackgroundColor: "#393939",
        primaryColor: "#161616",
        showBackgroundGradient: false,
      },
      header: {
        showResetButton: true,
        showAiDisclaimer: true,
        showMaximize: false,
      },

      // For anonymous access (security disabled), provide empty token
      authTokenNeeded: (event: any) => {
        event.authToken = "";
      },
    };

    const script = document.createElement("script");
    const scriptUrl = `${WXO_HOST_URL}/wxochat/wxoLoader.js?embed=true`;
    script.src = scriptUrl;
    script.async = true;

    console.log("Loading Watson Orchestrate script from:", scriptUrl);

    script.onload = () => {
      console.log("Watson Orchestrate script loaded successfully");
      try {
        if (window.wxoLoader) {
          window.wxoLoader.init();
          console.log("Watson Orchestrate chat initialized");
        }
      } catch (error) {
        console.error("Error initializing chat instance:", error);
      }
    };

    script.onerror = (error) => {
      console.error(
        "Failed to load watsonx Orchestrate script from:",
        scriptUrl
      );
      console.error("Error details:", error);
      console.error("Please verify:");
      console.error("1. VITE_WXO_HOST_URL is correct:", WXO_HOST_URL);
      console.error(
        "2. VITE_WXO_ORCHESTRATION_ID is correct:",
        WXO_ORCHESTRATION_ID
      );
      console.error("3. The Watson Orchestrate service is accessible");
    };

    document.body.appendChild(script);

    // Cleanup
    return () => {
      const container = document.getElementById(HTML_CONTAINER_ID);
      if (container) {
        container.style.display = "none";
      }
    };
  }, [onMessageReceived]);

  // Watch for sendMessage changes and send to chat
  useEffect(() => {
    if (chatInstance && sendMessage) {
      try {
        chatInstance.send(sendMessage);
      } catch (error) {
        console.error("Error sending message to chat:", error);
      }
    }
  }, [chatInstance, sendMessage]);

  return (
    <div className="h-full w-full" style={{ minHeight: "500px", backgroundColor: "#161616" }}>
      <Loading description="Booting watsonx Orchestrate" />
    </div>
  );
}

