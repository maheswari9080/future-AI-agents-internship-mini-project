/**
 * EWB Student Record Management System - Frontend SPA Application
 * Connects directly to FastAPI REST API endpoints
 */

document.addEventListener("DOMContentLoaded", () => {
  // Application State
  const state = {
    page: 1,
    limit: 10,
    total: 0,
    pages: 1,
    search: "",
    course: "",
    sortBy: "id",
    sortOrder: "desc",
    currentStudent: null,
    deleteTargetId: null,
  };

  // DOM Elements
  const el = {
    // Stats
    statTotalStudents: document.getElementById("stat-total-students"),
    statTotalCourses: document.getElementById("stat-total-courses"),
    statRecentEnrollments: document.getElementById("stat-recent-enrollments"),
    statAiStatus: document.getElementById("stat-ai-status"),
    directoryTotalBadge: document.getElementById("directory-total-badge"),

    // Filters
    filterSearch: document.getElementById("filter-search"),
    filterCourse: document.getElementById("filter-course"),
    btnRefresh: document.getElementById("btn-refresh"),

    // Table & States
    studentsTbody: document.getElementById("students-tbody"),
    emptyState: document.getElementById("empty-state"),
    loadingOverlay: document.getElementById("loading-overlay"),
    pageStart: document.getElementById("page-start"),
    pageEnd: document.getElementById("page-end"),
    pageTotal: document.getElementById("page-total"),
    pageIndicator: document.getElementById("page-indicator"),
    btnPagePrev: document.getElementById("btn-page-prev"),
    btnPageNext: document.getElementById("btn-page-next"),

    // Modals
    btnAddStudent: document.getElementById("btn-add-student"),
    btnEmptyAdd: document.getElementById("btn-empty-add"),
    studentModal: document.getElementById("student-modal"),
    modalTitle: document.getElementById("modal-title"),
    studentForm: document.getElementById("student-form"),
    modalBtnClose: document.getElementById("modal-btn-close"),
    modalBtnCancel: document.getElementById("modal-btn-cancel"),
    modalBtnSubmit: document.getElementById("modal-btn-submit"),

    // Form Fields
    formStudentId: document.getElementById("form-student-id"),
    formName: document.getElementById("form-name"),
    formDob: document.getElementById("form-dob"),
    formEnrollment: document.getElementById("form-enrollment"),
    formEmail: document.getElementById("form-email"),
    formPhone: document.getElementById("form-phone"),
    formCourse: document.getElementById("form-course"),
    formAddress: document.getElementById("form-address"),
    courseSuggestions: document.getElementById("course-suggestions"),

    // View Modal
    viewModal: document.getElementById("view-modal"),
    viewDetails: document.getElementById("view-details"),
    viewBtnClose: document.getElementById("view-btn-close"),
    viewBtnDismiss: document.getElementById("view-btn-dismiss"),
    viewBtnEdit: document.getElementById("view-btn-edit"),

    // Delete Modal
    deleteModal: document.getElementById("delete-modal"),
    deleteStudentName: document.getElementById("delete-student-name"),
    deleteBtnClose: document.getElementById("delete-btn-close"),
    deleteBtnCancel: document.getElementById("delete-btn-cancel"),
    deleteBtnConfirm: document.getElementById("delete-btn-confirm"),

    // AI Modal
    btnOpenAi: document.getElementById("btn-open-ai"),
    aiModal: document.getElementById("ai-modal"),
    aiBtnClose: document.getElementById("ai-btn-close"),
    aiInput: document.getElementById("ai-input"),
    aiBtnSend: document.getElementById("ai-btn-send"),
    aiResponseArea: document.getElementById("ai-response-area"),
    aiSourceBadge: document.getElementById("ai-source-badge"),
    aiResponseText: document.getElementById("ai-response-text"),

    // Toasts
    toastContainer: document.getElementById("toast-container"),
  };

  // Toast Notification Helper
  function showToast(message, type = "info") {
    const toast = document.createElement("div");
    toast.className = `toast toast-${type}`;
    const icon = type === "success" ? "✓" : type === "error" ? "✕" : "ℹ";
    toast.innerHTML = `<strong>${icon}</strong> <span>${escapeHtml(message)}</span>`;
    el.toastContainer.appendChild(toast);
    setTimeout(() => {
      toast.style.opacity = "0";
      toast.style.transition = "opacity 0.3s";
      setTimeout(() => toast.remove(), 300);
    }, 4000);
  }

  // Safe HTML Escaping for XSS Prevention
  function escapeHtml(str) {
    if (!str) return "";
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
  }

  // Fetch Dashboard Metrics
  async function fetchStats() {
    try {
      const res = await fetch("/students/stats");
      if (!res.ok) throw new Error("Failed to load statistics");
      const data = await res.json();

      el.statTotalStudents.textContent = data.total_students || 0;
      el.statTotalCourses.textContent = data.total_courses || 0;
      el.statRecentEnrollments.textContent = data.recent_enrollments_count || 0;
      el.directoryTotalBadge.textContent = `${data.total_students || 0} Students`;

      // Update courses filter dropdown and suggestions
      const currentVal = el.filterCourse.value;
      el.filterCourse.innerHTML = '<option value="">All Courses</option>';
      el.courseSuggestions.innerHTML = '';

      if (data.course_distribution) {
        Object.keys(data.course_distribution).forEach(courseName => {
          if (courseName && courseName !== "Unassigned") {
            const opt = document.createElement("option");
            opt.value = courseName;
            opt.textContent = `${courseName} (${data.course_distribution[courseName]})`;
            el.filterCourse.appendChild(opt);

            const datalistOpt = document.createElement("option");
            datalistOpt.value = courseName;
            el.courseSuggestions.appendChild(datalistOpt);
          }
        });
      }
      el.filterCourse.value = currentVal;
    } catch (err) {
      console.error("Stats fetch error:", err);
    }
  }

  // Check Ollama Status
  async function checkAiStatus() {
    try {
      const res = await fetch("/ai/status");
      if (res.ok) {
        const data = await res.json();
        if (data.available) {
          el.statAiStatus.textContent = "Ollama Active";
          el.statAiStatus.className = "stat-meta";
          el.statAiStatus.style.color = "#16a34a";
        } else {
          el.statAiStatus.textContent = "Offline fallback ready";
          el.statAiStatus.className = "stat-meta badge-offline";
        }
      }
    } catch (err) {
      el.statAiStatus.textContent = "Offline fallback ready";
    }
  }

  // Fetch Students Table Data
  async function fetchStudents() {
    el.loadingOverlay.classList.remove("hidden");
    try {
      const params = new URLSearchParams({
        page: state.page,
        limit: state.limit,
        sort_by: state.sortBy,
        sort_order: state.sortOrder,
      });

      if (state.search.trim()) params.append("search", state.search.trim());
      if (state.course) params.append("course", state.course);

      const res = await fetch(`/students?${params.toString()}`);
      if (!res.ok) throw new Error("Failed to fetch students list");
      const data = await res.json();

      state.total = data.total;
      state.pages = data.pages;
      renderTable(data.items);
      updatePagination();
    } catch (err) {
      console.error(err);
      showToast("Error loading student directory: " + err.message, "error");
    } finally {
      el.loadingOverlay.classList.add("hidden");
    }
  }

  // Render Table Rows
  function renderTable(students) {
    el.studentsTbody.innerHTML = "";
    if (!students || students.length === 0) {
      el.emptyState.classList.remove("hidden");
      return;
    }

    el.emptyState.classList.add("hidden");

    students.forEach(st => {
      const tr = document.createElement("tr");

      // ID
      const tdId = document.createElement("td");
      tdId.className = "col-id";
      tdId.textContent = `#${st.id}`;

      // Name
      const tdName = document.createElement("td");
      tdName.className = "col-name";
      tdName.textContent = st.name;

      // DOB
      const tdDob = document.createElement("td");
      tdDob.textContent = st.date_of_birth;

      // Contact
      const tdContact = document.createElement("td");
      tdContact.className = "col-contact";
      const contactDiv = document.createElement("div");
      contactDiv.className = "contact-badges";
      if (st.email) {
        const spanEmail = document.createElement("span");
        spanEmail.className = "badge";
        spanEmail.textContent = `✉ ${st.email}`;
        contactDiv.appendChild(spanEmail);
      }
      if (st.phone) {
        const spanPhone = document.createElement("span");
        spanPhone.className = "badge";
        spanPhone.textContent = `☎ ${st.phone}`;
        contactDiv.appendChild(spanPhone);
      }
      tdContact.appendChild(contactDiv);

      // Course
      const tdCourse = document.createElement("td");
      if (st.course) {
        const tag = document.createElement("span");
        tag.className = "course-tag";
        tag.textContent = st.course;
        tdCourse.appendChild(tag);
      } else {
        tdCourse.textContent = "—";
      }

      // Enrollment Date
      const tdEnroll = document.createElement("td");
      tdEnroll.textContent = st.enrollment_date || "—";

      // Actions
      const tdActions = document.createElement("td");
      tdActions.className = "col-actions";
      const actionDiv = document.createElement("div");
      actionDiv.className = "action-buttons";

      // View Button
      const btnView = document.createElement("button");
      btnView.className = "btn-table-action btn-view";
      btnView.textContent = "View";
      btnView.title = "View profile";
      btnView.onclick = () => openViewModal(st);

      // Edit Button
      const btnEdit = document.createElement("button");
      btnEdit.className = "btn-table-action btn-edit";
      btnEdit.textContent = "Edit";
      btnEdit.title = "Edit record";
      btnEdit.onclick = () => openEditModal(st);

      // Delete Button
      const btnDel = document.createElement("button");
      btnDel.className = "btn-table-action btn-delete";
      btnDel.textContent = "Delete";
      btnDel.title = "Delete record";
      btnDel.onclick = () => openDeleteModal(st);

      actionDiv.appendChild(btnView);
      actionDiv.appendChild(btnEdit);
      actionDiv.appendChild(btnDel);
      tdActions.appendChild(actionDiv);

      tr.appendChild(tdId);
      tr.appendChild(tdName);
      tr.appendChild(tdDob);
      tr.appendChild(tdContact);
      tr.appendChild(tdCourse);
      tr.appendChild(tdEnroll);
      tr.appendChild(tdActions);

      el.studentsTbody.appendChild(tr);
    });
  }

  // Update Pagination Controls
  function updatePagination() {
    const start = state.total === 0 ? 0 : (state.page - 1) * state.limit + 1;
    const end = Math.min(state.page * state.limit, state.total);

    el.pageStart.textContent = start;
    el.pageEnd.textContent = end;
    el.pageTotal.textContent = state.total;
    el.pageIndicator.textContent = `Page ${state.page} of ${Math.max(1, state.pages)}`;

    el.btnPagePrev.disabled = state.page <= 1;
    el.btnPageNext.disabled = state.page >= state.pages || state.total === 0;
  }

  // Clear Form Errors
  function clearErrors() {
    document.querySelectorAll(".form-error").forEach(span => span.textContent = "");
  }

  // Open Add Modal
  function openAddModal() {
    clearErrors();
    el.studentForm.reset();
    el.formStudentId.value = "";
    el.modalTitle.textContent = "Register New Student";
    el.modalBtnSubmit.textContent = "Save Student Record";
    el.studentModal.classList.remove("hidden");
  }

  // Open Edit Modal
  function openEditModal(student) {
    clearErrors();
    state.currentStudent = student;
    el.formStudentId.value = student.id;
    el.formName.value = student.name || "";
    el.formDob.value = student.date_of_birth || "";
    el.formEnrollment.value = student.enrollment_date || "";
    el.formEmail.value = student.email || "";
    el.formPhone.value = student.phone || "";
    el.formCourse.value = student.course || "";
    el.formAddress.value = student.address || "";

    el.modalTitle.textContent = `Edit Student #${student.id}`;
    el.modalBtnSubmit.textContent = "Update Student";
    el.studentModal.classList.remove("hidden");
  }

  // Open View Profile Modal
  function openViewModal(student) {
    state.currentStudent = student;
    el.viewDetails.innerHTML = "";

    const fields = [
      { label: "Student ID", val: `#${student.id}` },
      { label: "Full Name", val: student.name },
      { label: "Date of Birth", val: student.date_of_birth },
      { label: "Email Address", val: student.email || "Not provided" },
      { label: "Contact Phone", val: student.phone || "Not provided" },
      { label: "Course", val: student.course || "Not assigned" },
      { label: "Enrollment Date", val: student.enrollment_date || "Not set" },
      { label: "Address", val: student.address || "Not provided" },
      { label: "Created Timestamp", val: new Date(student.created_at).toLocaleString() },
      { label: "Last Updated", val: new Date(student.updated_at).toLocaleString() },
    ];

    fields.forEach(f => {
      const row = document.createElement("div");
      row.className = "view-row";
      row.innerHTML = `<span class="label">${escapeHtml(f.label)}</span><span class="val">${escapeHtml(f.val)}</span>`;
      el.viewDetails.appendChild(row);
    });

    el.viewModal.classList.remove("hidden");
  }

  // Open Delete Confirmation Modal
  function openDeleteModal(student) {
    state.deleteTargetId = student.id;
    el.deleteStudentName.textContent = `${student.name} (#${student.id})`;
    el.deleteModal.classList.remove("hidden");
  }

  // Close All Modals
  function closeModals() {
    el.studentModal.classList.add("hidden");
    el.viewModal.classList.add("hidden");
    el.deleteModal.classList.add("hidden");
    el.aiModal.classList.add("hidden");
  }

  // Form Submit Handler (Create & Update)
  el.studentForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    clearErrors();

    const id = el.formStudentId.value;
    const name = el.formName.value.trim();
    const dob = el.formDob.value;
    const email = el.formEmail.value.trim() || null;
    const phone = el.formPhone.value.trim() || null;
    const course = el.formCourse.value.trim() || null;
    const address = el.formAddress.value.trim() || null;
    const enrollment = el.formEnrollment.value || null;

    let hasErrors = false;

    if (!name) {
      document.getElementById("err-name").textContent = "Name is required.";
      hasErrors = true;
    }

    if (!dob) {
      document.getElementById("err-dob").textContent = "Date of birth is required.";
      hasErrors = true;
    } else {
      const dobDate = new Date(dob);
      const today = new Date();
      if (dobDate >= today) {
        document.getElementById("err-dob").textContent = "Date of birth must be in the past.";
        hasErrors = true;
      }
    }

    if (!email && !phone) {
      document.getElementById("err-email").textContent = "Provide at least an email or phone number.";
      document.getElementById("err-phone").textContent = "Provide at least an email or phone number.";
      hasErrors = true;
    }

    if (hasErrors) return;

    const payload = {
      name,
      date_of_birth: dob,
      email,
      phone,
      course,
      address,
      enrollment_date: enrollment,
    };

    el.modalBtnSubmit.disabled = true;
    el.modalBtnSubmit.textContent = "Saving...";

    try {
      const url = id ? `/students/${id}` : "/students";
      const method = id ? "PUT" : "POST";

      const res = await fetch(url, {
        method,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const errorData = await res.json();
        const msg = errorData.detail || "Operation failed.";
        showToast(Array.isArray(msg) ? msg[0].msg : msg, "error");
        return;
      }

      showToast(id ? "Student record updated successfully!" : "Student registered successfully!", "success");
      closeModals();
      await fetchStudents();
      await fetchStats();
    } catch (err) {
      showToast("Network error: " + err.message, "error");
    } finally {
      el.modalBtnSubmit.disabled = false;
      el.modalBtnSubmit.textContent = id ? "Update Student" : "Save Student Record";
    }
  });

  // Delete Confirmation Handler
  el.deleteBtnConfirm.addEventListener("click", async () => {
    if (!state.deleteTargetId) return;

    el.deleteBtnConfirm.disabled = true;
    el.deleteBtnConfirm.textContent = "Deleting...";

    try {
      const res = await fetch(`/students/${state.deleteTargetId}`, {
        method: "DELETE",
      });

      if (!res.ok && res.status !== 204) {
        const errData = await res.json();
        showToast(errData.detail || "Failed to delete student.", "error");
        return;
      }

      showToast("Student record deleted successfully.", "success");
      closeModals();
      await fetchStudents();
      await fetchStats();
    } catch (err) {
      showToast("Network error: " + err.message, "error");
    } finally {
      el.deleteBtnConfirm.disabled = false;
      el.deleteBtnConfirm.textContent = "Delete Record";
      state.deleteTargetId = null;
    }
  });

  // Search Filter with Debounce
  let searchTimer;
  el.filterSearch.addEventListener("input", (e) => {
    clearTimeout(searchTimer);
    searchTimer = setTimeout(() => {
      state.search = e.target.value;
      state.page = 1;
      fetchStudents();
    }, 300);
  });

  // Course Filter
  el.filterCourse.addEventListener("change", (e) => {
    state.course = e.target.value;
    state.page = 1;
    fetchStudents();
  });

  // Refresh Table Button
  el.btnRefresh.addEventListener("click", () => {
    fetchStudents();
    fetchStats();
    checkAiStatus();
    showToast("Directory refreshed", "info");
  });

  // Pagination Next / Prev
  el.btnPagePrev.addEventListener("click", () => {
    if (state.page > 1) {
      state.page--;
      fetchStudents();
    }
  });

  el.btnPageNext.addEventListener("click", () => {
    if (state.page < state.pages) {
      state.page++;
      fetchStudents();
    }
  });

  // Modal Open/Close Triggers
  el.btnAddStudent.addEventListener("click", openAddModal);
  el.btnEmptyAdd.addEventListener("click", openAddModal);
  el.modalBtnClose.addEventListener("click", closeModals);
  el.modalBtnCancel.addEventListener("click", closeModals);

  el.viewBtnClose.addEventListener("click", closeModals);
  el.viewBtnDismiss.addEventListener("click", closeModals);
  el.viewBtnEdit.addEventListener("click", () => {
    closeModals();
    if (state.currentStudent) openEditModal(state.currentStudent);
  });

  el.deleteBtnClose.addEventListener("click", closeModals);
  el.deleteBtnCancel.addEventListener("click", closeModals);

  // AI Modal Triggers
  el.btnOpenAi.addEventListener("click", () => {
    el.aiModal.classList.remove("hidden");
    el.aiInput.focus();
  });
  el.aiBtnClose.addEventListener("click", closeModals);

  // Suggested Prompt Chips
  document.querySelectorAll(".chip").forEach(chip => {
    chip.addEventListener("click", () => {
      el.aiInput.value = chip.dataset.query;
      sendAiQuestion();
    });
  });

  // Send AI Question
  async function sendAiQuestion() {
    const question = el.aiInput.value.trim();
    if (!question || question.length < 3) {
      showToast("Please enter a question of at least 3 characters", "error");
      return;
    }

    el.aiBtnSend.disabled = true;
    el.aiBtnSend.textContent = "Analyzing...";
    el.aiResponseArea.classList.remove("hidden");
    el.aiResponseText.textContent = "Querying academic database...";
    el.aiSourceBadge.textContent = "Processing...";

    try {
      const res = await fetch("/ai/ask", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question }),
      });

      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || "AI service returned an error.");
      }

      const data = await res.json();
      el.aiSourceBadge.textContent = data.source;
      el.aiResponseText.textContent = data.answer;
    } catch (err) {
      el.aiSourceBadge.textContent = "Error";
      el.aiResponseText.textContent = "Unable to process query: " + err.message;
    } finally {
      el.aiBtnSend.disabled = false;
      el.aiBtnSend.textContent = "Ask";
    }
  }

  el.aiBtnSend.addEventListener("click", sendAiQuestion);
  el.aiInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") sendAiQuestion();
  });

  // Close modals on clicking outside overlay
  window.addEventListener("click", (e) => {
    if (e.target.classList.contains("modal-overlay")) {
      closeModals();
    }
  });

  // Escape key closes modals
  window.addEventListener("keydown", (e) => {
    if (e.key === "Escape") closeModals();
  });

  // Initial Load
  fetchStats();
  checkAiStatus();
  fetchStudents();
});
