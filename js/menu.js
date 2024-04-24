import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";
import { ComfyDialog, $el } from "../../scripts/ui.js";
export var griptape_instance = null;

export function setGriptapeInstance(obj) {
  griptape_instance = obj;
}
const envKeys = [
  "OPENAI_API_KEY",
  "GOOGLE_API_KEY",
  "AWS_ACCESS_KEY",
  "AWS_SECRET_ACCESS_KEY",
  "LEONARDO_API_KEY",
  "GROQ_API_KEY",
];

function createEnvVarFields(keys) {
  return keys.map((key) => {
    return $el("div", {}, [
      $el(
        "label",
        { for: key, className: "griptape-label" },
        key.replace(/_/g, " ")
      ),
      $el("input", {
        type: "text",
        id: key,
        className: "griptape-input",
        value: "",
      }), // Assuming you would fill in the value somehow
    ]);
  });
}

var docStyle = document.createElement("style");
docStyle.innerHTML = `
// .griptape-modal {
//     position: fixed;
//     top: 0;
//     left: 0;
//     right: 0;
//     bottom: 0;
//     width: 100%;
//     height: 100%;
//     display: flex;
//     justify-content: center;
//     align-items: center;
//     background-color: rgba(0, 0, 0, 0.7);
//   }
  #griptape-dialog {
    width: 50%;
  }
  .griptape-inner-container {
    // background-color: #fff;
    padding: 20px;
    border-radius: 8px;
    box-sizing: border-box;
    width: 100%; /* Adjust based on content up to max-width */
    height: 100%;
    font-family: Lato;
    // max-width: 90%; /* Don't exceed 90% of the viewport width */
    // max-height: 90%; /* Don't exceed 90% of the viewport height */
    overflow: auto; /* Allows scrolling within the modal if content is too large */
    color: #d1d1d1;
  }
   .griptape-title {
    font-size: 24px;
    font-weight: bold;
    margin-bottom: 20px;
    text-align: center;
    } 
  .griptape-close-button {
    position: absolute;
    top: 10px;
    right: 10px;
    border: none;
    background-color: transparent;
    color: #333;
    font-size: 24px;
    cursor: pointer;
  }
  
  .griptape-modal-content {
    width: 100%;
  }
  
  .griptape-textarea {
    width: 100%;
    height: 100%;
    margin-top: 5px;
    margin-bottom: 20px;
    background-color: #262626;
    color: #c3c3c3;
    border: none;
    border-radius: 8px;
    padding: 8px;
  }
  
  .griptape-button-container {
    display: flex;
    justify-content: space-between;
  }
  
  .griptape-load-button, .griptape-save-button {
    padding: 10px;
    border-radius: 5px;
    background-color: #007BFF;
    color: white;
    border: none;
  }
  
  .griptape-load-button:hover, .griptape-save-button:hover {
    background-color: #0056b3;
  }
  .griptape-label {
    display: block;
    margin-top: 10px;
    font-weight: bold;
  }
  
  .griptape-input {
    width: 100%;
    padding: 8px;
    margin-top: 5px;
    box-sizing: border-box; /* Ensures the padding doesn't affect the width */
  }

  `;

document.head.appendChild(docStyle);
class GriptapeDialog extends ComfyDialog {
  constructor() {
    super();

    // Create close button with "X" label, using the 'griptape-' prefix
    const closeButton = $el("button", {
      className: "griptape-close-button",
      type: "button",
      textContent: "X",
      onclick: () => this.close(),
    });

    // Main content container with the 'griptape-' prefix
    const content = $el(
      "div",
      {
        className: "griptape-modal-content",
      },
      [
        $el(
          "div",
          {
            className: "griptape-title",
          },
          "Griptape Configuration"
        ),
        ...createEnvVarFields(envKeys), // Spread the array returned by createEnvVarFields into the parent div
        // $el(
        //   "label",
        //   { className: "griptape-label" },
        //   "ADDITIONAL ENVIRONMENT VARIABLES"
        // ),
        // $el("textarea", {
        //   className: "griptape-textarea",
        //   placeholder: "Enter environment variables...",
        //   rows: 10,
        //   cols: 50,
        // }),
        $el(
          "div",
          {
            className: "griptape-button-container",
          },
          [
            $el("button", {
              type: "button",
              className: "griptape-load-button",
              textContent: "Load",
            }),
            $el("button", {
              type: "button",
              className: "griptape-save-button",
              textContent: "Save",
            }),
          ]
        ),
      ]
    );

    // Inner container to hold the content and the close button
    const innerContainer = $el(
      "div",
      {
        className: "griptape-inner-container",
      },
      [closeButton, content]
    );

    // Append inner container to the modal
    this.element = $el(
      "div",
      {
        className: "comfy-modal",
        id: "griptape-dialog",
      },
      [innerContainer]
    );

    // Append this.element to document.body
    document.body.appendChild(this.element);
  }

  show() {
    this.element.style.display = "block";
  }
  close() {
    this.element.style.display = "none";
  }
}
app.registerExtension({
  name: "Griptape.ConfigButton",
  async setup(app) {
    const menu = document.querySelector(".comfy-menu");
    const hr = document.createElement("hr");

    hr.style.margin = "8px 0";
    hr.style.width = "100%";
    menu.append(hr);

    const configButton = document.createElement("button");
    configButton.id = "griptape-config-button";
    configButton.textContent = "Griptape Configuration";

    configButton.onclick = async () => {
      if (!griptape_instance) setGriptapeInstance(new GriptapeDialog());
      griptape_instance.show();
    };
    menu.append(configButton);
  },
});
