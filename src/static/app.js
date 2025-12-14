document.addEventListener("DOMContentLoaded", () => {
  const activitiesList = document.getElementById("activities-list");
  const activitySelect = document.getElementById("activity");
  const signupForm = document.getElementById("signup-form");
  const messageDiv = document.getElementById("message");
  const authStatus = document.getElementById("auth-status");
  const loginContainer = document.getElementById("login-container");
  const appContent = document.getElementById("app-content");

  let currentUser = null;

  // Check authentication status
  async function checkAuth() {
    try {
      const response = await fetch("/auth/user", {
        credentials: "include"
      });
      
      if (response.ok) {
        currentUser = await response.json();
        showAuthenticatedUI();
        return true;
      } else {
        showLoginUI();
        return false;
      }
    } catch (error) {
      console.error("Error checking auth:", error);
      showLoginUI();
      return false;
    }
  }

  function showAuthenticatedUI() {
    loginContainer.classList.add("hidden");
    appContent.classList.remove("hidden");
    
    authStatus.innerHTML = `
      <div style="display: flex; align-items: center; justify-content: center; gap: 10px; margin-top: 10px;">
        ${currentUser.avatar_url ? `<img src="${currentUser.avatar_url}" alt="Avatar" style="width: 30px; height: 30px; border-radius: 50%;">` : ''}
        <span>Welcome, ${currentUser.name || currentUser.email}!</span>
        <button onclick="logout()" style="padding: 5px 10px; font-size: 14px;">Logout</button>
      </div>
    `;
  }

  function showLoginUI() {
    loginContainer.classList.remove("hidden");
    appContent.classList.add("hidden");
    authStatus.innerHTML = '<p style="margin-top: 10px; font-size: 14px;">Not signed in</p>';
  }

  // Logout function (make it global so the button can call it)
  window.logout = async function() {
    try {
      await fetch("/auth/logout", {
        method: "POST",
        credentials: "include"
      });
      currentUser = null;
      window.location.reload();
    } catch (error) {
      console.error("Error logging out:", error);
    }
  };

  // Function to fetch activities from API
  async function fetchActivities() {
    try {
      const response = await fetch("/activities");
      const activities = await response.json();

      // Clear loading message
      activitiesList.innerHTML = "";

      // Clear activity select dropdown (keep the first default option)
      activitySelect.innerHTML = '<option value="">-- Select an activity --</option>';

      // Populate activities list
      Object.entries(activities).forEach(([name, details]) => {
        const activityCard = document.createElement("div");
        activityCard.className = "activity-card";

        const spotsLeft = details.max_participants - details.participants.length;

        // Build participants list HTML
        let participantsHTML = '';
        if (details.participants.length > 0) {
          participantsHTML = `
            <div class="participants-section">
              <strong>Participants:</strong>
              <ul class="participants-list">
                ${details.participants.map(email => {
                  // Show delete button only for current user's own registration
                  const canDelete = currentUser && email === currentUser.email;
                  return `
                    <li class="participant-item">
                      <span class="participant-email">${email}</span>
                      ${canDelete ? `<button class="delete-btn" data-activity="${name}" data-email="${email}" title="Remove participant">✖</button>` : ''}
                    </li>
                  `;
                }).join('')}
              </ul>
            </div>
          `;
        } else {
          participantsHTML = `
            <div class="participants-section">
              <strong>Participants:</strong>
              <p class="no-participants">No participants yet. Be the first to sign up!</p>
            </div>
          `;
        }

        activityCard.innerHTML = `
          <h4>${name}</h4>
          <p>${details.description}</p>
          <p><strong>Schedule:</strong> ${details.schedule}</p>
          <p><strong>Availability:</strong> ${spotsLeft} spots left</p>
          ${participantsHTML}
        `;

        activitiesList.appendChild(activityCard);

        // Add option to select dropdown
        const option = document.createElement("option");
        option.value = name;
        option.textContent = name;
        activitySelect.appendChild(option);
      });

      // Add event listeners to delete buttons
      document.querySelectorAll('.delete-btn').forEach(button => {
        button.addEventListener('click', handleDeleteParticipant);
      });
    } catch (error) {
      activitiesList.innerHTML = "<p>Failed to load activities. Please try again later.</p>";
      console.error("Error fetching activities:", error);
    }
  }

  // Handle delete participant
  async function handleDeleteParticipant(event) {
    const button = event.target;
    const activity = button.getAttribute('data-activity');
    const email = button.getAttribute('data-email');

    if (!confirm(`Are you sure you want to unregister from ${activity}?`)) {
      return;
    }

    try {
      const response = await fetch(
        `/activities/${encodeURIComponent(activity)}/unregister?email=${encodeURIComponent(email)}`,
        {
          method: "DELETE",
          credentials: "include"
        }
      );

      const result = await response.json();

      if (response.ok) {
        messageDiv.textContent = result.message;
        messageDiv.className = "success";
        messageDiv.classList.remove("hidden");

        // Refresh activities list
        fetchActivities();

        // Hide message after 5 seconds
        setTimeout(() => {
          messageDiv.classList.add("hidden");
        }, 5000);
      } else {
        messageDiv.textContent = result.detail || "An error occurred";
        messageDiv.className = "error";
        messageDiv.classList.remove("hidden");
      }
    } catch (error) {
      messageDiv.textContent = "Failed to unregister. Please try again.";
      messageDiv.className = "error";
      messageDiv.classList.remove("hidden");
      console.error("Error unregistering:", error);
    }
  }

  // Handle form submission
  signupForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const activity = document.getElementById("activity").value;

    try {
      const response = await fetch(
        `/activities/${encodeURIComponent(activity)}/signup`,
        {
          method: "POST",
          credentials: "include"
        }
      );

      const result = await response.json();

      if (response.ok) {
        messageDiv.textContent = result.message;
        messageDiv.className = "success";
        signupForm.reset();
      } else {
        messageDiv.textContent = result.detail || "An error occurred";
        messageDiv.className = "error";
      }

      messageDiv.classList.remove("hidden");

      // Hide message after 5 seconds
      setTimeout(() => {
        messageDiv.classList.add("hidden");
      }, 5000);

      // Refresh activities list to show updated participant count
      fetchActivities();
    } catch (error) {
      messageDiv.textContent = "Failed to sign up. Please try again.";
      messageDiv.className = "error";
      messageDiv.classList.remove("hidden");
      console.error("Error signing up:", error);
    }
  });

  // Check for error parameter in URL
  const urlParams = new URLSearchParams(window.location.search);
  const error = urlParams.get('error');
  if (error) {
    messageDiv.textContent = `Authentication error: ${error}`;
    messageDiv.className = "error";
    messageDiv.classList.remove("hidden");
    
    // Clean URL
    window.history.replaceState({}, document.title, window.location.pathname);
  }

  // Initialize app
  checkAuth().then(isAuthenticated => {
    if (isAuthenticated) {
      fetchActivities();
    }
  });
});
