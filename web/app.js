/**
 * ErrandMate Modern Full-Stack Web Application Client
 * Pure Vanilla JavaScript ES6+ Architecture with Autonomous AI Engine Integration
 */

// Application State
const state = {
  user: null,
  token: localStorage.getItem("errandmate_token") || null,
  currentView: "dashboard",
  myTasksTab: "posted",
  currentTaskDetail: null,
  activeRatingScore: 5,
  selectedCategory: "All",
  lastSuggestedPrice: null,
  aiTelemetry: null,
};

const CATEGORIES = [
  { name: "All", icon: "layers" },
  { name: "Pet Care", icon: "dog" },
  { name: "Grocery Shopping", icon: "shopping-cart" },
  { name: "Delivery / Courier", icon: "package" },
  { name: "Pharmacy Pickup", icon: "pill" },
  { name: "House Cleaning", icon: "sparkles" },
  { name: "Gardening", icon: "flower-2" },
  { name: "Moving Help", icon: "truck" },
  { name: "Tech Support", icon: "laptop" },
  { name: "Cooking / Meal Prep", icon: "utensils" },
  { name: "Car Wash", icon: "car" },
  { name: "Laundry", icon: "shirt" },
  { name: "Other", icon: "help-circle" },
];

// ==================== INITIALIZATION ====================

document.addEventListener("DOMContentLoaded", async () => {
  setupEventListeners();
  initCategoryPills();
  updateGreeting();
  await checkServerHealth();
  await updateAITelemetryBadge();

  if (state.token) {
    await fetchCurrentUser();
  } else {
    updateAuthUI();
  }

  navigate("dashboard");
});

function setupEventListeners() {
  const searchInput = document.getElementById("explore-search");
  const sortSelect = document.getElementById("explore-sort");

  if (searchInput) searchInput.addEventListener("input", debounce(() => loadExploreTasks(), 250));
  if (sortSelect) sortSelect.addEventListener("change", () => loadExploreTasks());
}

function initCategoryPills() {
  const bar = document.getElementById("category-pills-bar");
  if (!bar) return;

  bar.innerHTML = CATEGORIES.map(cat => {
    const isActive = cat.name === state.selectedCategory;
    return `
      <button onclick="selectCategoryFilter('${cat.name}')" class="category-pill flex items-center space-x-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold whitespace-nowrap border ${
        isActive ? 'active bg-indigo-600 text-white border-indigo-600' : 'bg-slate-50 text-slate-700 border-slate-200 hover:bg-slate-100'
      }">
        <i data-lucide="${cat.icon}" class="w-3.5 h-3.5"></i>
        <span>${cat.name}</span>
      </button>
    `;
  }).join("");

  refreshIcons();
}

function selectCategoryFilter(catName) {
  state.selectedCategory = catName;
  initCategoryPills();
  loadExploreTasks();
}

function updateGreeting() {
  const hour = new Date().getHours();
  let timeStr = "Good morning";
  if (hour >= 12 && hour < 17) timeStr = "Good afternoon";
  else if (hour >= 17) timeStr = "Good evening";

  const greetingEl = document.getElementById("greeting-text");
  if (greetingEl) {
    const name = state.user ? state.user.full_name.split(" ")[0] : "Neighbor";
    greetingEl.innerText = `${timeStr}, ${name}!`;
  }
}

// ==================== API CLIENT ====================

async function apiFetch(endpoint, options = {}) {
  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {}),
  };

  if (state.token) {
    headers["Authorization"] = `Bearer ${state.token}`;
  }

  try {
    const response = await fetch(endpoint, {
      ...options,
      headers,
    });

    if (response.status === 401) {
      if (state.token) {
        showToast("Session expired. Please sign in again.", true);
        logout();
      }
      throw new Error("Unauthorized");
    }

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || "An error occurred.");
    }
    return data;
  } catch (err) {
    console.error(`API Error on ${endpoint}:`, err);
    throw err;
  }
}

async function checkServerHealth() {
  try {
    const health = await apiFetch("/api/health");
    const statusText = document.getElementById("server-status-text");
    if (statusText) statusText.innerText = "Platform Online";
  } catch (e) {
    const statusText = document.getElementById("server-status-text");
    if (statusText) statusText.innerText = "Reconnecting...";
  }
}

// ==================== AUTHENTICATION & DEMO PERSONAS ====================

async function fetchCurrentUser() {
  try {
    const user = await apiFetch("/api/auth/me");
    state.user = user;
    updateAuthUI();
    updateGreeting();
  } catch (err) {
    state.user = null;
    state.token = null;
    localStorage.removeItem("errandmate_token");
    updateAuthUI();
  }
}

function updateAuthUI() {
  const guestBox = document.getElementById("auth-guest");
  const userBox = document.getElementById("auth-user");

  if (state.user) {
    if (guestBox) guestBox.classList.add("hidden");
    if (userBox) userBox.classList.remove("hidden");

    const avatar = document.getElementById("user-avatar");
    const nameDisplay = document.getElementById("user-name-display");
    const roleText = document.getElementById("user-role-text");

    if (avatar) avatar.innerText = state.user.full_name.charAt(0).toUpperCase();
    if (nameDisplay) nameDisplay.innerText = state.user.full_name;
    if (roleText) {
      roleText.innerText = state.user.is_id_verified
        ? `Verified (${state.user.id_type || 'ID'})`
        : `Role: ${state.user.role}`;
    }
  } else {
    if (guestBox) guestBox.classList.remove("hidden");
    if (userBox) userBox.classList.add("hidden");
  }

  refreshIcons();
}

async function handleLoginSubmit(e) {
  e.preventDefault();
  const email = document.getElementById("login-email").value.trim();
  const password = document.getElementById("login-password").value;

  try {
    const res = await apiFetch("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });

    state.token = res.access_token;
    state.user = res.user;
    localStorage.setItem("errandmate_token", res.access_token);

    closeModal("modal-login");
    updateAuthUI();
    updateGreeting();
    showToast(`Signed in: Welcome back, ${res.user.full_name}!`);
    navigate(state.currentView);
  } catch (err) {
    showToast(err.message || "Invalid login credentials", true);
  }
}

async function handleAdminQuickLogin() {
  try {
    const res = await apiFetch("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ email: "admin", password: "admin123" }),
    });

    state.token = res.access_token;
    state.user = res.user;
    localStorage.setItem("errandmate_token", res.access_token);

    closeModal("modal-login");
    updateAuthUI();
    updateGreeting();
    showToast("👑 Logged in as Platform Administrator!");
    navigate("dashboard");
  } catch (err) {
    showToast("Admin login failed: " + err.message, true);
  }
}

async function handleRegisterSubmit(e) {
  e.preventDefault();
  const full_name = document.getElementById("reg-name").value.trim();
  const email = document.getElementById("reg-email").value.trim();
  const phone = document.getElementById("reg-phone").value.trim();
  const residential_address = document.getElementById("reg-address").value.trim();
  const postcode = document.getElementById("reg-postcode").value.trim().toUpperCase();
  const id_type = document.getElementById("reg-id-type").value;
  const id_number = document.getElementById("reg-id-number").value.trim();
  const password = document.getElementById("reg-pw").value;
  const password_confirm = document.getElementById("reg-pw2").value;
  const role = document.getElementById("reg-role").value;

  if (password !== password_confirm) {
    showToast("Passwords do not match.", true);
    return;
  }

  if (!residential_address || !postcode || !id_number) {
    showToast("Please provide your physical address and ID number for community verification.", true);
    return;
  }

  try {
    const res = await apiFetch("/api/auth/register", {
      method: "POST",
      body: JSON.stringify({
        full_name,
        email,
        phone,
        password,
        role,
        residential_address,
        postcode,
        id_type,
        id_number,
      }),
    });

    state.token = res.access_token;
    state.user = res.user;
    localStorage.setItem("errandmate_token", res.access_token);

    closeModal("modal-register");
    updateAuthUI();
    updateGreeting();
    showToast(`Account verified & created! Welcome to ErrandMate, ${res.user.full_name}!`);
    navigate("dashboard");
  } catch (err) {
    showToast(err.message || "Registration failed", true);
  }
}

function logout() {
  state.user = null;
  state.token = null;
  localStorage.removeItem("errandmate_token");
  updateAuthUI();
  updateGreeting();
  showToast("You have been signed out.");
  navigate("dashboard");
}

async function switchDemoPersona(email) {
  if (!email) return;

  if (email === "admin") {
    await handleAdminQuickLogin();
    return;
  }

  try {
    const res = await apiFetch("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password: "Password123!" }),
    });

    state.token = res.access_token;
    state.user = res.user;
    localStorage.setItem("errandmate_token", res.access_token);

    updateAuthUI();
    updateGreeting();
    showToast(`Switched persona to: ${res.user.full_name} (${res.user.role})`);
    navigate(state.currentView);
  } catch (err) {
    showToast("Failed to switch demo persona", true);
  }
}

function quickFillLogin(email, pw) {
  document.getElementById("login-email").value = email;
  document.getElementById("login-password").value = pw;
}

// ==================== AI ASSISTANT & SMART POST ====================

function fillAIPrompt(text) {
  const input = document.getElementById("ai-quick-prompt");
  if (input) {
    input.value = text;
    handleAIErrandDraft();
  }
}

function openSmartPostPrompt() {
  navigate("dashboard");
  const input = document.getElementById("ai-quick-prompt");
  if (input) {
    input.focus();
    input.scrollIntoView({ behavior: "smooth", block: "center" });
    input.classList.add("ring-2", "ring-purple-400");
    setTimeout(() => input.classList.remove("ring-2", "ring-purple-400"), 2000);
  }
}

async function handleAIErrandDraft() {
  const input = document.getElementById("ai-quick-prompt");
  if (!input || !input.value.trim()) {
    showToast("Please enter an errand description first.", true);
    return;
  }

  const promptText = input.value.trim();
  showToast("✨ Categorizing Address, Task & Time...", false);

  try {
    const res = await apiFetch("/api/ai/parse-intent", {
      method: "POST",
      body: JSON.stringify({ prompt: promptText }),
    });

    if (!res.is_valid) {
      showToast(`Moderation Notice: ${res.error || "Cannot process prompt"}`, true);
      return;
    }

    const { extracted, categorized_entities } = res;

    // Show interactive extraction preview on the dashboard
    const previewBox = document.getElementById("ai-extraction-preview");
    if (previewBox && categorized_entities) {
      document.getElementById("ai-preview-address").innerText = categorized_entities.address || "Cardiff";
      document.getElementById("ai-preview-task").innerText = `${categorized_entities.task} (${categorized_entities.category})`;
      document.getElementById("ai-preview-time").innerText = categorized_entities.time || "Flexible";

      const keywordsContainer = document.getElementById("ai-preview-keywords");
      if (keywordsContainer && categorized_entities.keywords) {
        keywordsContainer.innerHTML = categorized_entities.keywords.map(kw => `
          <span class="px-2 py-0.5 rounded-full bg-purple-900/60 text-purple-200 border border-purple-500/30 text-[10px] font-semibold">
            ${escapeHtml(kw)}
          </span>
        `).join("");
      }

      previewBox.classList.remove("hidden");
    }

    // Pre-populate Post Task modal
    document.getElementById("post-title").value = extracted.title || "";
    document.getElementById("post-category").value = extracted.category || "Other";
    document.getElementById("post-location").value = extracted.location || "";
    document.getElementById("post-price").value = extracted.price || 16.0;
    document.getElementById("post-deadline").value = extracted.deadline || "Flexible";
    document.getElementById("post-description").value = extracted.description || "";

    // Trigger price estimation to display fair range
    triggerPriceEstimation();

    showToast(`✨ Categorized: ${categorized_entities.task} at ${categorized_entities.address}`);
    await updateAITelemetryBadge();
  } catch (err) {
    showToast("Intent extraction failed: " + err.message, true);
  }
}

let priceEstimateTimeout = null;
function triggerPriceEstimation() {
  clearTimeout(priceEstimateTimeout);
  priceEstimateTimeout = setTimeout(async () => {
    const category = document.getElementById("post-category")?.value || "Other";
    const title = document.getElementById("post-title")?.value || "";
    const description = document.getElementById("post-description")?.value || "";
    const deadline = document.getElementById("post-deadline")?.value || "";
    const user_price = parseFloat(document.getElementById("post-price")?.value) || null;

    try {
      const data = await apiFetch("/api/ai/estimate-price", {
        method: "POST",
        body: JSON.stringify({ category, title, description, deadline, user_price }),
      });

      state.lastSuggestedPrice = data.recommended_price;

      const estimateEl = document.getElementById("ai-price-estimate");
      const detailEl = document.getElementById("ai-price-detail");
      if (estimateEl) {
        estimateEl.innerText = `£${data.price_range.min.toFixed(2)} - £${data.price_range.max.toFixed(2)} (~${data.estimated_duration_minutes} mins)`;
      }
      if (detailEl) {
        detailEl.innerText = `${data.assessment_detail} (${data.complexity_tier} Complexity)`;
      }
    } catch (e) {
      console.warn("Pricing estimate note:", e);
    }
  }, 300);
}

function applySuggestedPrice() {
  if (state.lastSuggestedPrice) {
    document.getElementById("post-price").value = state.lastSuggestedPrice.toFixed(2);
    triggerPriceEstimation();
    showToast(`Applied recommended rate: £${state.lastSuggestedPrice.toFixed(2)}`);
  }
}

// ==================== AI TELEMETRY MODAL & CONTROLS ====================

async function updateAITelemetryBadge() {
  try {
    const telem = await apiFetch("/api/ai/telemetry");
    state.aiTelemetry = telem;
    const badge = document.getElementById("header-ai-status");
    if (badge) {
      badge.innerText = telem.status === "active" ? "Active" : "Paused";
      badge.className = telem.status === "active" ? "text-[10px] bg-purple-500/30 text-purple-200 px-1.5 rounded" : "text-[10px] bg-slate-700 text-slate-300 px-1.5 rounded";
    }
  } catch (e) {
    console.warn("Telemetry poll:", e);
  }
}

async function openAITelemetryModal() {
  try {
    const telem = await apiFetch("/api/ai/telemetry");
    state.aiTelemetry = telem;

    document.getElementById("telemetry-agent-state").innerText = telem.status === "active" ? "Running & Autonomous Dispatch Active" : "Paused / Monitoring Only";
    document.getElementById("btn-toggle-agent").innerText = telem.status === "active" ? "Pause Agent" : "Activate Agent";

    document.getElementById("telem-nlp").innerText = telem.telemetry.nlp_extractions_count;
    document.getElementById("telem-pricing").innerText = telem.telemetry.pricing_queries_count;
    document.getElementById("telem-crosschecks").innerText = telem.telemetry.autonomous_crosschecks_count;
    document.getElementById("telem-dispatches").innerText = telem.telemetry.ai_dispatches_count;

    openModal("modal-ai-telemetry");
  } catch (err) {
    showToast("Could not load Telemetry", true);
  }
}

async function toggleAIAgentMode() {
  if (!state.user) {
    showToast("Please sign in to configure Autonomous Agent mode", true);
    openLoginModal();
    return;
  }
  try {
    const res = await apiFetch("/api/ai/toggle-agent", { method: "POST" });
    showToast(`Autonomous Agent is now ${res.status}`);
    openAITelemetryModal();
    updateAITelemetryBadge();
  } catch (err) {
    showToast(err.message || "Failed to toggle agent", true);
  }
}

// ==================== NAVIGATION ====================

function navigate(viewName) {
  state.currentView = viewName;

  ["dashboard", "explore", "mytasks", "profile"].forEach(v => {
    const el = document.getElementById(`view-${v}`);
    if (el) {
      if (v === viewName) {
        el.classList.remove("hidden");
        el.classList.add("fade-in");
      } else {
        el.classList.add("hidden");
        el.classList.remove("fade-in");
      }
    }
  });

  document.querySelectorAll(".nav-btn").forEach(btn => {
    if (btn.dataset.nav === viewName) {
      btn.classList.add("bg-indigo-50", "text-indigo-600");
      btn.classList.remove("text-slate-700");
    } else {
      btn.classList.remove("bg-indigo-50", "text-indigo-600");
      btn.classList.add("text-slate-700");
    }
  });

  if (viewName === "dashboard") loadDashboard();
  if (viewName === "explore") loadExploreTasks();
  if (viewName === "mytasks") loadMyTasks();
  if (viewName === "profile") loadProfile();

  refreshIcons();
}

// ==================== DASHBOARD ====================

async function loadDashboard() {
  try {
    const stats = await apiFetch("/api/stats/dashboard");
    document.getElementById("stat-open-tasks").innerText = stats.total_open_tasks;
    document.getElementById("stat-posted-tasks").innerText = stats.my_posted_tasks;
    document.getElementById("stat-active-tasks").innerText = stats.my_active_tasks;
    document.getElementById("stat-completed-tasks").innerText = stats.my_completed_tasks;
    document.getElementById("stat-earnings").innerText = `£${stats.my_earnings.toFixed(2)}`;

    const tasks = await apiFetch("/api/tasks?status=open&limit=6&sort=newest");
    const container = document.getElementById("dashboard-recent-tasks");
    if (!container) return;

    if (tasks.length === 0) {
      container.innerHTML = `
        <div class="col-span-full text-center py-12 bg-slate-50 rounded-2xl border border-dashed border-slate-200">
          <i data-lucide="inbox" class="w-8 h-8 text-slate-400 mx-auto mb-2"></i>
          <p class="text-sm font-semibold text-slate-700">No open errands right now.</p>
          <p class="text-xs text-slate-400 mt-1">Be the first to post a task or try the AI Smart Draft above!</p>
          <button onclick="openPostTaskModal()" class="mt-4 px-4 py-2 rounded-xl bg-indigo-600 text-white text-xs font-semibold hover:bg-indigo-700">Post Errand</button>
        </div>
      `;
    } else {
      container.innerHTML = tasks.map(t => renderTaskCard(t, "dashboard")).join("");
    }
  } catch (err) {
    console.error("Dashboard load failed:", err);
  }
  refreshIcons();
}

// ==================== EXPLORE MARKETPLACE ====================

async function loadExploreTasks() {
  const search = document.getElementById("explore-search")?.value || "";
  const sort = document.getElementById("explore-sort")?.value || "newest";
  const category = state.selectedCategory;

  let url = `/api/tasks?status=open&sort=${sort}`;
  if (category && category !== "All") url += `&category=${encodeURIComponent(category)}`;
  if (search.trim()) url += `&search=${encodeURIComponent(search.trim())}`;

  try {
    const tasks = await apiFetch(url);
    const grid = document.getElementById("explore-tasks-grid");
    if (!grid) return;

    if (tasks.length === 0) {
      grid.innerHTML = `
        <div class="col-span-full text-center py-16 bg-white rounded-2xl border border-slate-200 p-8 shadow-sm">
          <i data-lucide="search-x" class="w-10 h-10 text-slate-400 mx-auto mb-3"></i>
          <h3 class="text-base font-bold text-slate-800">No errands found matching "${escapeHtml(category)}"</h3>
          <p class="text-xs text-slate-500 mt-1">Try selecting another category pill or clearing the search bar.</p>
          <button onclick="selectCategoryFilter('All')" class="mt-4 px-4 py-2 rounded-xl bg-indigo-50 text-indigo-700 text-xs font-semibold">View All Errands</button>
        </div>
      `;
    } else {
      grid.innerHTML = tasks.map(t => renderTaskCard(t, "explore")).join("");
    }
  } catch (err) {
    console.error("Explore load failed:", err);
  }
  refreshIcons();
}

// ==================== MY TASKS ====================

function setMyTasksTab(tab) {
  state.myTasksTab = tab;
  document.querySelectorAll(".mytasks-tab-btn").forEach(btn => {
    if (btn.dataset.tab === tab) {
      btn.className = "mytasks-tab-btn pb-3 px-1 text-sm font-semibold border-b-2 border-indigo-600 text-indigo-600 whitespace-nowrap";
    } else {
      btn.className = "mytasks-tab-btn pb-3 px-1 text-sm font-semibold border-b-2 border-transparent text-slate-500 hover:text-slate-700 whitespace-nowrap";
    }
  });
  loadMyTasks();
}

async function loadMyTasks() {
  if (!state.user) {
    const container = document.getElementById("mytasks-list");
    if (container) {
      container.innerHTML = `
        <div class="text-center py-16 bg-white rounded-2xl border border-slate-200 p-8 shadow-sm">
          <i data-lucide="lock" class="w-10 h-10 text-indigo-500 mx-auto mb-3"></i>
          <h3 class="text-lg font-bold text-slate-800">Sign in to track your errands</h3>
          <p class="text-xs text-slate-500 mt-1 mb-4">View tasks you have created, jobs you are running, and manage completions.</p>
          <button onclick="openLoginModal()" class="px-5 py-2.5 rounded-xl bg-indigo-600 text-white font-semibold text-sm hover:bg-indigo-700 shadow">Sign In</button>
        </div>
      `;
    }
    refreshIcons();
    return;
  }

  try {
    const tasks = await apiFetch(`/api/tasks/user/summary?tab=${state.myTasksTab}`);
    const container = document.getElementById("mytasks-list");
    if (!container) return;

    if (tasks.length === 0) {
      const messages = {
        posted: "You haven't posted any errands yet.",
        running: "You don't have any active errands in progress.",
        done: "No completed errands yet.",
        cancelled: "No cancelled errands.",
      };
      container.innerHTML = `
        <div class="text-center py-14 bg-white rounded-2xl border border-slate-200 p-8 shadow-sm">
          <i data-lucide="calendar-check" class="w-10 h-10 text-slate-400 mx-auto mb-3"></i>
          <h3 class="text-base font-bold text-slate-800">${messages[state.myTasksTab]}</h3>
          ${state.myTasksTab === "posted" ? '<button onclick="openPostTaskModal()" class="mt-4 px-4 py-2 rounded-xl bg-indigo-600 text-white text-xs font-semibold">Post Errand</button>' : ''}
          ${state.myTasksTab === "running" ? '<button onclick="navigate(\'explore\')" class="mt-4 px-4 py-2 rounded-xl bg-indigo-600 text-white text-xs font-semibold">Find Errands to Run</button>' : ''}
        </div>
      `;
    } else {
      container.innerHTML = tasks.map(t => renderMyTaskRow(t)).join("");
    }
  } catch (err) {
    console.error("My tasks load failed:", err);
  }
  refreshIcons();
}

// ==================== PROFILE ====================

async function loadProfile() {
  if (!state.user) {
    navigate("dashboard");
    openLoginModal();
    return;
  }

  document.getElementById("profile-card-avatar").innerText = state.user.full_name.charAt(0).toUpperCase();
  document.getElementById("profile-card-name").innerText = state.user.full_name;
  document.getElementById("profile-card-email").innerText = state.user.email;
  document.getElementById("profile-card-done").innerText = state.user.tasks_done;
  document.getElementById("profile-card-joined").innerText = state.user.joined_date ? state.user.joined_date.substring(0, 10) : "2026";

  const idBadge = document.getElementById("profile-card-id-badge");
  if (idBadge) {
    idBadge.innerText = `Verified: ${state.user.id_type || "Passport"}`;
  }

  const postcodeEl = document.getElementById("profile-card-postcode");
  if (postcodeEl) {
    postcodeEl.innerText = state.user.postcode || "CF24 9ZZ";
  }

  document.getElementById("profile-name").value = state.user.full_name;
  document.getElementById("profile-phone").value = state.user.phone;
  document.getElementById("profile-role").value = state.user.role;

  try {
    const pub = await apiFetch(`/api/users/${state.user.id}`);
    document.getElementById("profile-card-rating").innerText = pub.average_rating ? `★ ${pub.average_rating}/5` : "No ratings yet";
  } catch (e) {
    document.getElementById("profile-card-rating").innerText = "--";
  }
}

async function handleUpdateProfile(e) {
  e.preventDefault();
  const full_name = document.getElementById("profile-name").value.trim();
  const phone = document.getElementById("profile-phone").value.trim();
  const role = document.getElementById("profile-role").value;

  try {
    const updated = await apiFetch("/api/users/profile", {
      method: "PUT",
      body: JSON.stringify({ full_name, phone, role }),
    });
    state.user = { ...state.user, ...updated };
    updateAuthUI();
    loadProfile();
    showToast("Profile successfully updated!");
  } catch (err) {
    showToast(err.message || "Failed to update profile", true);
  }
}

async function handleChangePassword(e) {
  e.preventDefault();
  const old_password = document.getElementById("pw-old").value;
  const new_password = document.getElementById("pw-new").value;
  const confirm_password = document.getElementById("pw-confirm").value;

  if (new_password !== confirm_password) {
    showToast("New passwords do not match", true);
    return;
  }

  try {
    await apiFetch("/api/users/change-password", {
      method: "POST",
      body: JSON.stringify({ old_password, new_password }),
    });
    document.getElementById("password-form").reset();
    showToast("Password changed successfully!");
  } catch (err) {
    showToast(err.message || "Password update failed", true);
  }
}

// ==================== TASK CREATION & DETAILS ====================

async function handleCreateTask(e) {
  e.preventDefault();
  if (!state.user) {
    closeModal("modal-post-task");
    openLoginModal();
    return;
  }

  const title = document.getElementById("post-title").value.trim();
  const category = document.getElementById("post-category").value;
  const price = parseFloat(document.getElementById("post-price").value);
  const location = document.getElementById("post-location").value.trim();
  const deadline = document.getElementById("post-deadline").value.trim();
  const description = document.getElementById("post-description").value.trim();

  try {
    await apiFetch("/api/tasks", {
      method: "POST",
      body: JSON.stringify({ title, category, price, location, deadline, description }),
    });

    closeModal("modal-post-task");
    e.target.reset();
    showToast("Errand posted successfully!");
    navigate("mytasks");
  } catch (err) {
    showToast(err.message || "Failed to post task", true);
  }
}

async function openTaskDetails(taskId) {
  try {
    const task = await apiFetch(`/api/tasks/${taskId}`);
    state.currentTaskDetail = task;

    document.getElementById("detail-title").innerText = task.title;
    document.getElementById("detail-price").innerText = `£${task.price.toFixed(2)}`;
    document.getElementById("detail-category-badge").innerText = task.category || "Other";

    const statusBadge = document.getElementById("detail-status-badge");
    statusBadge.innerText = formatStatus(task.status);
    statusBadge.className = `px-2.5 py-0.5 rounded-full text-xs font-semibold badge-${task.status}`;

    // Render 5-stage Stepper Visualizer
    renderStepper(task.status);

    document.getElementById("detail-location").innerText = task.location;
    document.getElementById("detail-deadline").innerText = task.deadline || "Flexible";
    document.getElementById("detail-poster").innerText = `${task.poster_name} (ID Verified)`;
    document.getElementById("detail-runner").innerText = task.runner_name ? `${task.runner_name} (ID Verified)` : "Unassigned";
    document.getElementById("detail-description").innerText = task.description || "No specific instructions provided.";

    // Cancellation banner
    const cancelBanner = document.getElementById("detail-cancellation-banner");
    if (task.status === "cancelled" && task.cancellation_reason) {
      cancelBanner.classList.remove("hidden");
      document.getElementById("detail-cancellation-reason").innerText = task.cancellation_reason;
    } else {
      cancelBanner.classList.add("hidden");
    }

    // AI Runner Matching Section (Show to task poster for Open tasks)
    const isPoster = state.user && state.user.id === task.poster_id;
    const aiSection = document.getElementById("detail-ai-matching-section");
    if (task.status === "open" && isPoster) {
      aiSection.classList.remove("hidden");
      loadAIMatches(task.id);
    } else {
      aiSection.classList.add("hidden");
    }

    // Autonomous Verification & Crosscheck Audit Box
    loadAICrosscheck(task);

    // Action Buttons
    const actionsBox = document.getElementById("detail-actions");
    actionsBox.innerHTML = renderTaskActions(task);

    openModal("modal-task-details");
    refreshIcons();
  } catch (err) {
    showToast("Could not load task details", true);
  }
}

function renderStepper(currentStatus) {
  const steps = [
    { key: "open", label: "Open" },
    { key: "accepted", label: "Accepted" },
    { key: "in_progress", label: "In Progress" },
    { key: "awaiting_confirmation", label: "Awaiting Conf." },
    { key: "completed", label: "Completed" },
  ];

  const statusIndexMap = {
    open: 0,
    accepted: 1,
    in_progress: 2,
    awaiting_confirmation: 3,
    completed: 4,
    cancelled: -1,
  };

  const currIdx = statusIndexMap[currentStatus] ?? 0;
  const container = document.getElementById("task-stepper-container");
  if (!container) return;

  if (currentStatus === "cancelled") {
    container.innerHTML = `
      <div class="w-full text-center py-2 text-xs font-bold text-red-600 bg-red-50 rounded-lg">
        ❌ Errand Cancelled
      </div>
    `;
    return;
  }

  container.innerHTML = steps.map((s, idx) => {
    let stateClass = "";
    if (idx < currIdx) stateClass = "completed";
    else if (idx === currIdx) stateClass = "active";

    return `
      <div class="stepper-step ${stateClass}">
        <div class="stepper-circle">
          ${idx < currIdx ? '✓' : idx + 1}
        </div>
        <span class="text-[10px] font-semibold mt-1 ${idx === currIdx ? 'text-indigo-600 font-bold' : 'text-slate-500'}">${s.label}</span>
      </div>
    `;
  }).join("");
}

async function loadAIMatches(taskId) {
  const listEl = document.getElementById("ai-matches-list");
  if (!listEl) return;
  listEl.innerHTML = `<div class="text-xs text-slate-400 py-2">✨ Computing multi-criteria affinity scores...</div>`;

  try {
    const data = await apiFetch(`/api/ai/match-runners/${taskId}`);
    if (!data.matches || data.matches.length === 0) {
      listEl.innerHTML = `<div class="text-xs text-slate-500 py-1">No registered runners available right now.</div>`;
      return;
    }

    listEl.innerHTML = data.matches.map((m, idx) => `
      <div class="bg-white p-3 rounded-xl border border-slate-200 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div class="space-y-1">
          <div class="flex items-center space-x-2">
            <span class="text-sm font-bold text-slate-900">${escapeHtml(m.full_name)}</span>
            <span class="px-2 py-0.5 rounded-full text-[10px] font-extrabold ${m.match_score_percent >= 85 ? 'bg-emerald-100 text-emerald-800' : 'bg-indigo-100 text-indigo-800'}">
              ${m.match_score_percent}% Match
            </span>
            ${m.average_rating ? `<span class="text-xs font-semibold text-amber-600">★ ${m.average_rating}</span>` : ''}
          </div>
          <div class="flex flex-wrap gap-1">
            ${m.xai_reasons.map(r => `<span class="text-[10px] px-1.5 py-0.5 rounded bg-slate-100 text-slate-600 font-medium">${escapeHtml(r)}</span>`).join("")}
          </div>
        </div>
        ${idx === 0 ? `
          <button onclick="executeAutonomousDispatch(${taskId})" class="px-3.5 py-2 rounded-lg bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 text-white font-bold text-xs shadow transition whitespace-nowrap flex items-center space-x-1.5 self-start sm:self-center">
            <i data-lucide="zap" class="w-3.5 h-3.5"></i>
            <span>Autonomous Dispatch</span>
          </button>
        ` : ''}
      </div>
    `).join("");

    refreshIcons();
  } catch (e) {
    listEl.innerHTML = `<div class="text-xs text-red-500">Could not retrieve candidate matches.</div>`;
  }
}

async function executeAutonomousDispatch(taskId) {
  try {
    const res = await apiFetch(`/api/ai/autonomous-dispatch/${taskId}`, { method: "POST" });
    showToast(`⚡ ${res.reasoning}`);
    await updateAITelemetryBadge();
    openTaskDetails(taskId);
    if (state.currentView === "mytasks") loadMyTasks();
  } catch (err) {
    showToast(err.message || "Autonomous dispatch failed", true);
  }
}

async function loadAICrosscheck(task) {
  const pill = document.getElementById("crosscheck-verdict-pill");
  const summary = document.getElementById("crosscheck-summary-text");
  const checklist = document.getElementById("crosscheck-checklist-container");

  try {
    const audit = await apiFetch(`/api/ai/crosscheck/${task.id}`, { method: "POST" });
    if (pill) {
      pill.innerText = `${audit.confidence_score}% - ${audit.verdict.replace(/_/g, " ")}`;
      pill.className = `px-2.5 py-0.5 rounded-full text-[11px] font-bold ${
        audit.badge_color === 'emerald' ? 'bg-emerald-100 text-emerald-800' : (audit.badge_color === 'amber' ? 'bg-amber-100 text-amber-800' : 'bg-red-100 text-red-800')
      }`;
    }
    if (summary) summary.innerText = audit.summary;

    if (checklist) {
      checklist.innerHTML = audit.checklist.map(c => `
        <div class="flex items-start space-x-2">
          <span class="font-bold ${c.status === 'PASS' ? 'text-emerald-600' : (c.status === 'WARN' ? 'text-amber-600' : 'text-blue-500')}">
            ${c.status === 'PASS' ? '✓' : (c.status === 'WARN' ? '!' : '•')}
          </span>
          <span class="text-slate-600"><strong class="text-slate-800">${escapeHtml(c.check)}:</strong> ${escapeHtml(c.detail)}</span>
        </div>
      `).join("");
    }
  } catch (e) {
    if (summary) summary.innerText = "Audit pipeline active.";
  }
}

function renderTaskActions(task) {
  const isPoster = state.user && state.user.id === task.poster_id;
  const isRunner = state.user && state.user.id === task.runner_id;
  let buttons = [];

  if (task.status === "open" && !isPoster) {
    buttons.push(`<button onclick="acceptTask(${task.id})" class="px-4 py-2 rounded-xl bg-emerald-600 text-white font-semibold text-xs hover:bg-emerald-700 shadow">Accept Errand</button>`);
  }
  if (task.status === "accepted" && isRunner) {
    buttons.push(`<button onclick="startTask(${task.id})" class="px-4 py-2 rounded-xl bg-indigo-600 text-white font-semibold text-xs hover:bg-indigo-700 shadow">Start Errand</button>`);
    buttons.push(`<button onclick="abandonTask(${task.id})" class="px-4 py-2 rounded-xl bg-red-100 text-red-700 font-semibold text-xs hover:bg-red-200">Abandon</button>`);
  }
  if (task.status === "in_progress" && isRunner) {
    buttons.push(`<button onclick="submitTask(${task.id})" class="px-4 py-2 rounded-xl bg-emerald-600 text-white font-semibold text-xs hover:bg-emerald-700 shadow">Submit Completion</button>`);
    buttons.push(`<button onclick="abandonTask(${task.id})" class="px-4 py-2 rounded-xl bg-red-100 text-red-700 font-semibold text-xs hover:bg-red-200">Abandon</button>`);
  }
  if (task.status === "awaiting_confirmation" && isPoster) {
    buttons.push(`<button onclick="confirmTask(${task.id})" class="px-4 py-2 rounded-xl bg-emerald-600 text-white font-semibold text-xs hover:bg-emerald-700 shadow">Confirm Completion</button>`);
  }
  if (task.status === "completed" && isPoster && task.runner_id) {
    buttons.push(`<button onclick="openRateModal(${task.id}, '${escapeHtml(task.runner_name || "Runner")}')" class="px-4 py-2 rounded-xl bg-amber-500 text-white font-semibold text-xs hover:bg-amber-600 shadow">Rate Runner</button>`);
  }
  if (["open", "accepted"].includes(task.status) && isPoster) {
    buttons.push(`<button onclick="cancelTaskPrompt(${task.id})" class="px-4 py-2 rounded-xl bg-red-600 text-white font-semibold text-xs hover:bg-red-700">Cancel Errand</button>`);
  }

  return buttons.join("");
}

// ==================== TASK LIFECYCLE ACTIONS ====================

async function acceptTask(taskId) {
  if (!state.user) {
    openLoginModal();
    return;
  }
  try {
    await apiFetch(`/api/tasks/${taskId}/accept`, { method: "POST" });
    closeModal("modal-task-details");
    showToast("Errand accepted! Check My Tasks to begin.");
    navigate("mytasks");
    setMyTasksTab("running");
  } catch (err) {
    showToast(err.message || "Failed to accept task", true);
  }
}

async function startTask(taskId) {
  try {
    await apiFetch(`/api/tasks/${taskId}/start`, { method: "POST" });
    closeModal("modal-task-details");
    showToast("Errand is now in progress!");
    loadMyTasks();
  } catch (err) {
    showToast(err.message, true);
  }
}

async function submitTask(taskId) {
  try {
    await apiFetch(`/api/tasks/${taskId}/submit`, { method: "POST" });
    closeModal("modal-task-details");
    showToast("Submitted! The poster will confirm completion.");
    loadMyTasks();
  } catch (err) {
    showToast(err.message, true);
  }
}

async function confirmTask(taskId) {
  if (!confirm("Are you sure you want to confirm this errand is completed?")) return;
  try {
    await apiFetch(`/api/tasks/${taskId}/confirm`, { method: "POST" });
    closeModal("modal-task-details");
    showToast("Errand confirmed completed!");
    loadMyTasks();
  } catch (err) {
    showToast(err.message, true);
  }
}

async function abandonTask(taskId) {
  if (!confirm("Give up this errand and return it to open marketplace listings?")) return;
  try {
    await apiFetch(`/api/tasks/${taskId}/abandon`, { method: "POST" });
    closeModal("modal-task-details");
    showToast("Errand returned to marketplace.");
    loadMyTasks();
  } catch (err) {
    showToast(err.message, true);
  }
}

async function cancelTaskPrompt(taskId) {
  const reason = prompt("Optional reason for cancellation:");
  if (reason === null) return;
  try {
    await apiFetch(`/api/tasks/${taskId}/cancel`, {
      method: "POST",
      body: JSON.stringify({ reason: reason.trim() }),
    });
    closeModal("modal-task-details");
    showToast("Errand cancelled.");
    loadMyTasks();
  } catch (err) {
    showToast(err.message, true);
  }
}

// ==================== RATINGS ====================

function openRateModal(taskId, runnerName) {
  document.getElementById("rate-task-id").value = taskId;
  document.getElementById("rate-runner-name").innerText = runnerName;
  document.getElementById("rate-review").value = "";
  setRatingValue(5);
  closeModal("modal-task-details");
  openModal("modal-rate");
}

function setRatingValue(val) {
  state.activeRatingScore = val;
  document.getElementById("rate-score").value = val;
  const stars = document.querySelectorAll("#star-selector .star");
  stars.forEach((star, idx) => {
    if (idx < val) {
      star.className = "star text-amber-400";
    } else {
      star.className = "star text-slate-300";
    }
  });
}

async function handleRateSubmit(e) {
  e.preventDefault();
  const task_id = parseInt(document.getElementById("rate-task-id").value);
  const rating = parseInt(document.getElementById("rate-score").value);
  const review = document.getElementById("rate-review").value.trim();

  try {
    await apiFetch("/api/ratings", {
      method: "POST",
      body: JSON.stringify({ task_id, rating, review }),
    });
    closeModal("modal-rate");
    showToast("Thank you! Runner review submitted.");
  } catch (err) {
    showToast(err.message || "Failed to submit rating", true);
  }
}

// ==================== COMPONENT RENDERERS ====================

function renderTaskCard(task, context) {
  const isPoster = state.user && state.user.id === task.poster_id;
  const canAccept = task.status === "open" && !isPoster;

  return `
    <div class="task-card bg-white rounded-2xl border border-slate-200 p-5 flex flex-col justify-between shadow-sm">
      <div>
        <div class="flex items-start justify-between gap-3 mb-2.5">
          <span class="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-slate-100 text-slate-700">${escapeHtml(task.category || "Other")}</span>
          <span class="text-lg font-black text-indigo-600">£${task.price.toFixed(2)}</span>
        </div>
        <h3 class="text-base font-bold text-slate-900 line-clamp-1 mb-1">${escapeHtml(task.title)}</h3>
        <p class="text-xs text-slate-500 line-clamp-2 mb-4">${escapeHtml(task.description || "No specific instructions.")}</p>
      </div>

      <div class="pt-3 border-t border-slate-100 space-y-3">
        <div class="text-[11px] text-slate-500 flex items-center justify-between">
          <span class="flex items-center space-x-1">
            <i data-lucide="map-pin" class="w-3.5 h-3.5 text-slate-400"></i>
            <span class="truncate max-w-[130px]">${escapeHtml(task.location)}</span>
          </span>
          <span class="flex items-center space-x-1">
            <i data-lucide="clock" class="w-3.5 h-3.5 text-slate-400"></i>
            <span>${escapeHtml(task.deadline || "Flexible")}</span>
          </span>
        </div>

        <div class="flex items-center justify-between gap-2">
          <button onclick="openTaskDetails(${task.id})" class="flex-1 py-2 text-xs font-semibold rounded-xl border border-slate-200 text-slate-700 hover:bg-slate-50 transition">
            Details
          </button>
          ${canAccept ? `
            <button onclick="acceptTask(${task.id})" class="flex-1 py-2 text-xs font-semibold rounded-xl bg-indigo-600 text-white hover:bg-indigo-700 transition shadow-sm">
              Accept
            </button>
          ` : ''}
        </div>
      </div>
    </div>
  `;
}

function renderMyTaskRow(task) {
  const isPoster = state.user && state.user.id === task.poster_id;
  const actionsHtml = renderTaskActions(task);

  return `
    <div class="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm space-y-3">
      <div class="flex flex-col md:flex-row md:items-center justify-between gap-3">
        <div class="space-y-1">
          <div class="flex items-center space-x-2">
            <span class="px-2.5 py-0.5 rounded-full text-xs font-semibold badge-${task.status}">${formatStatus(task.status)}</span>
            <span class="text-xs text-slate-400">•</span>
            <span class="text-xs font-medium text-slate-500">${escapeHtml(task.category || "Other")}</span>
            <span class="text-xs text-slate-400">•</span>
            <span class="text-xs font-medium text-slate-500">📍 ${escapeHtml(task.location)}</span>
          </div>
          <h3 class="text-base font-bold text-slate-900">${escapeHtml(task.title)}</h3>
          <p class="text-xs text-slate-500">
            ${isPoster ? `Assigned Runner: <strong>${escapeHtml(task.runner_name || "Unassigned")}</strong>` : `Posted by: <strong>${escapeHtml(task.poster_name)}</strong>`}
            ${task.deadline ? ` • Deadline: ${escapeHtml(task.deadline)}` : ""}
          </p>
        </div>

        <div class="flex items-center justify-between md:justify-end space-x-4 border-t md:border-t-0 pt-3 md:pt-0 border-slate-100">
          <span class="text-lg font-black text-indigo-600">£${task.price.toFixed(2)}</span>
          <div class="flex items-center space-x-2">
            <button onclick="openTaskDetails(${task.id})" class="px-3.5 py-2 text-xs font-semibold rounded-xl border border-slate-200 text-slate-700 hover:bg-slate-50">
              Details
            </button>
            ${actionsHtml}
          </div>
        </div>
      </div>
    </div>
  `;
}

// ==================== MODAL HELPERS ====================

function openModal(id) {
  const modal = document.getElementById(id);
  if (modal) modal.classList.remove("hidden");
  refreshIcons();
}

function closeModal(id) {
  const modal = document.getElementById(id);
  if (modal) modal.classList.add("hidden");
}

function openPostTaskModal() {
  if (!state.user) {
    openLoginModal();
    return;
  }
  openModal("modal-post-task");
  triggerPriceEstimation();
}

function openLoginModal() {
  closeModal("modal-register");
  openModal("modal-login");
}

function openRegisterModal() {
  closeModal("modal-login");
  openModal("modal-register");
}

function switchAuthModal(target) {
  if (target === "login") openLoginModal();
  else openRegisterModal();
}

// ==================== TOAST NOTIFICATIONS ====================

let toastTimeout = null;
function showToast(msg, isError = false) {
  const toast = document.getElementById("toast");
  const toastMsg = document.getElementById("toast-msg");
  const toastIcon = document.getElementById("toast-icon");

  if (!toast || !toastMsg) return;

  toastMsg.innerText = msg;
  if (isError) {
    toastIcon.innerHTML = '<i data-lucide="alert-circle" class="w-5 h-5 text-red-400"></i>';
  } else {
    toastIcon.innerHTML = '<i data-lucide="check-circle" class="w-5 h-5 text-emerald-400"></i>';
  }
  refreshIcons();

  toast.classList.add("show");
  clearTimeout(toastTimeout);
  toastTimeout = setTimeout(() => {
    toast.classList.remove("show");
  }, 4000);
}

// ==================== UTILITIES ====================

function formatStatus(status) {
  const map = {
    open: "Open",
    accepted: "Accepted",
    in_progress: "In Progress",
    awaiting_confirmation: "Awaiting Confirmation",
    completed: "Completed",
    cancelled: "Cancelled",
  };
  return map[status] || status;
}

function escapeHtml(str) {
  if (!str) return "";
  return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

function debounce(func, wait) {
  let timeout;
  return function (...args) {
    clearTimeout(timeout);
    timeout = setTimeout(() => func.apply(this, args), wait);
  };
}

function refreshIcons() {
  if (window.lucide) {
    lucide.createIcons();
  }
}
