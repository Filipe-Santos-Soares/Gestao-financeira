const STORAGE_KEY = "gestao-financeira-v1";

const salaryInput = document.querySelector("#salaryInput");
const salaryHint = document.querySelector("#salaryHint");
const fixedBody = document.querySelector("#fixedExpensesBody");
const variableBody = document.querySelector("#variableExpensesBody");
const rowTemplate = document.querySelector("#expenseRowTemplate");
const chartCanvas = document.querySelector("#financeChart");
const evolutionChartCanvas = document.querySelector("#evolutionChart");
const chartEmpty = document.querySelector("#chartEmpty");
const evolutionEmpty = document.querySelector("#evolutionEmpty");
const chartLegend = document.querySelector("#chartLegend");
const statusMessage = document.querySelector("#statusMessage");
const balanceRow = document.querySelector("#balanceRow");
const clearDataButton = document.querySelector("#clearDataButton");
const saveBudgetButton = document.querySelector("#saveBudgetButton");
const duplicatePreviousButton = document.querySelector("#duplicatePreviousButton");
const periodMonthInput = document.querySelector("#periodMonth");
const periodYearInput = document.querySelector("#periodYear");
const feedbackPopup = document.querySelector("#feedbackPopup");
const feedbackPopupMessage = document.querySelector("#feedbackPopupMessage");
const feedbackPopupClose = document.querySelector("#feedbackPopupClose");
const savedMonthsList = document.querySelector("#savedMonthsList");
const savedMonthsEmpty = document.querySelector("#savedMonthsEmpty");
const refreshSavedMonthsButton = document.querySelector("#refreshSavedMonthsButton");
const compareBaseMonth = document.querySelector("#compareBaseMonth");
const compareTargetMonth = document.querySelector("#compareTargetMonth");
const comparisonEmpty = document.querySelector("#comparisonEmpty");
const comparisonList = document.querySelector("#comparisonList");
const categoryForm = document.querySelector("#categoryForm");
const categoryNameInput = document.querySelector("#categoryNameInput");
const categoryTypeInput = document.querySelector("#categoryTypeInput");
const categorySubmitButton = document.querySelector("#categorySubmitButton");
const categoryCancelButton = document.querySelector("#categoryCancelButton");
const categoryStatus = document.querySelector("#categoryStatus");
const categoryList = document.querySelector("#categoryList");
const fixedCategoryOptions = document.querySelector("#fixedCategoryOptions");
const variableCategoryOptions = document.querySelector("#variableCategoryOptions");
const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content || "";

const summaryFields = {
  salary: document.querySelector("#summarySalary"),
  fixed: document.querySelector("#summaryFixed"),
  variable: document.querySelector("#summaryVariable"),
  total: document.querySelector("#summaryTotal"),
  balance: document.querySelector("#summaryBalance"),
  committed: document.querySelector("#summaryCommitted"),
  available: document.querySelector("#summaryAvailable"),
};

const comparisonFields = {
  salary: document.querySelector("#comparisonSalary"),
  fixed: document.querySelector("#comparisonFixed"),
  variable: document.querySelector("#comparisonVariable"),
  total: document.querySelector("#comparisonTotal"),
  balance: document.querySelector("#comparisonBalance"),
};

let financeChart = null;
let evolutionChart = null;
let refreshTimer = null;
let rowCounter = 0;
let isRestoringState = false;
let periodChangeTimer = null;
let savedMonthBudgets = [];
let categories = [];
let editingCategoryId = null;

const chartColors = ["#147d64", "#d97706", "#3b82f6"];
const categoryTypeLabels = {
  fixed: "Fixo",
  variable: "Variado",
  both: "Ambos",
};

const currencyFormatter = new Intl.NumberFormat("pt-BR", {
  style: "currency",
  currency: "BRL",
});

const percentFormatter = new Intl.NumberFormat("pt-BR", {
  minimumFractionDigits: 2,
  maximumFractionDigits: 2,
});

function getDefaultPeriod() {
  const now = new Date();

  return {
    month: now.getMonth() + 1,
    year: now.getFullYear(),
  };
}

function formatPeriod(month, year) {
  return `${String(month).padStart(2, "0")}/${year}`;
}

function getSelectedPeriod() {
  const fallback = getDefaultPeriod();
  const month = Number(periodMonthInput.value);
  const year = Number(periodYearInput.value);

  return {
    month: month >= 1 && month <= 12 ? month : fallback.month,
    year: year >= 1900 ? year : fallback.year,
  };
}

function setSelectedPeriod(month, year) {
  periodMonthInput.value = String(month);
  periodYearInput.value = String(year);
  updatePeriodLabel();
}

function getPreviousPeriod(period) {
  if (period.month === 1) {
    return {
      month: 12,
      year: period.year - 1,
    };
  }

  return {
    month: period.month - 1,
    year: period.year,
  };
}

function updatePeriodLabel() {
  const currentMonth = document.querySelector("#currentMonth");
  const { month, year } = getSelectedPeriod();
  const formatter = new Intl.DateTimeFormat("pt-BR", {
    month: "long",
    year: "numeric",
  });

  currentMonth.textContent = formatter.format(new Date(year, month - 1, 1));
}

function showFeedbackPopup(message) {
  feedbackPopupMessage.textContent = message;
  feedbackPopup.hidden = false;
}

function hideFeedbackPopup() {
  feedbackPopup.hidden = true;
  feedbackPopupMessage.textContent = "";
}

function jsonHeaders(includeCsrf = false) {
  const headers = {
    "Content-Type": "application/json",
  };

  if (includeCsrf && csrfToken) {
    headers["X-CSRF-Token"] = csrfToken;
  }

  return headers;
}

function periodKey(budget) {
  return `${budget.year}-${String(budget.month).padStart(2, "0")}`;
}

function getBudgetByKey(key) {
  return savedMonthBudgets.find((budget) => periodKey(budget) === key);
}

function renderComparisonOption(select, budget) {
  const option = document.createElement("option");
  option.value = periodKey(budget);
  option.textContent = formatPeriod(budget.month, budget.year);
  select.appendChild(option);
}

function renderComparisonControls() {
  compareBaseMonth.innerHTML = "";
  compareTargetMonth.innerHTML = "";

  if (savedMonthBudgets.length < 2) {
    comparisonEmpty.hidden = false;
    comparisonList.hidden = true;
    return;
  }

  savedMonthBudgets.forEach((budget) => {
    renderComparisonOption(compareBaseMonth, budget);
    renderComparisonOption(compareTargetMonth, budget);
  });

  compareTargetMonth.value = periodKey(savedMonthBudgets[0]);
  compareBaseMonth.value = periodKey(savedMonthBudgets[1]);
  renderComparison();
}

function renderComparisonValue(element, value, positiveIsGood = true) {
  element.classList.remove("is-positive", "is-negative");
  element.textContent = `${value >= 0 ? "+" : "-"}${currencyFormatter.format(Math.abs(value))}`;

  if (value === 0) {
    return;
  }

  element.classList.add(value > 0 === positiveIsGood ? "is-positive" : "is-negative");
}

function renderComparison() {
  const baseBudget = getBudgetByKey(compareBaseMonth.value);
  const targetBudget = getBudgetByKey(compareTargetMonth.value);

  if (!baseBudget || !targetBudget || baseBudget === targetBudget) {
    comparisonEmpty.hidden = false;
    comparisonEmpty.textContent = "Selecione dois meses diferentes para comparar.";
    comparisonList.hidden = true;
    return;
  }

  comparisonEmpty.hidden = true;
  comparisonEmpty.textContent = "Salve pelo menos dois meses para comparar.";
  comparisonList.hidden = false;

  renderComparisonValue(comparisonFields.salary, targetBudget.salary - baseBudget.salary);
  renderComparisonValue(comparisonFields.fixed, targetBudget.fixed_total - baseBudget.fixed_total, false);
  renderComparisonValue(comparisonFields.variable, targetBudget.variable_total - baseBudget.variable_total, false);
  renderComparisonValue(comparisonFields.total, targetBudget.total_expenses - baseBudget.total_expenses, false);
  renderComparisonValue(comparisonFields.balance, targetBudget.remaining_balance - baseBudget.remaining_balance);
}

function renderEvolutionChart() {
  const hasEvolutionData = savedMonthBudgets.length >= 2;
  evolutionEmpty.classList.toggle("is-hidden", hasEvolutionData);

  if (!window.Chart || !hasEvolutionData) {
    if (evolutionChart) {
      evolutionChart.destroy();
      evolutionChart = null;
    }
    return;
  }

  const chartBudgets = [...savedMonthBudgets].reverse();
  const labels = chartBudgets.map((budget) => formatPeriod(budget.month, budget.year));
  const expenseValues = chartBudgets.map((budget) => budget.total_expenses);
  const balanceValues = chartBudgets.map((budget) => budget.remaining_balance);

  if (!evolutionChart) {
    evolutionChart = new Chart(evolutionChartCanvas, {
      type: "line",
      data: {
        labels,
        datasets: [
          {
            label: "Total de gastos",
            data: expenseValues,
            borderColor: "#d97706",
            backgroundColor: "rgba(217, 119, 6, 0.12)",
            tension: 0.25,
            fill: true,
          },
          {
            label: "Saldo",
            data: balanceValues,
            borderColor: "#147d64",
            backgroundColor: "rgba(20, 125, 100, 0.12)",
            tension: 0.25,
            fill: true,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          tooltip: {
            callbacks: {
              label: (context) => `${context.dataset.label}: ${currencyFormatter.format(context.parsed.y || 0)}`,
            },
          },
        },
        scales: {
          y: {
            ticks: {
              callback: (value) => currencyFormatter.format(value),
            },
          },
        },
      },
    });
    return;
  }

  evolutionChart.data.labels = labels;
  evolutionChart.data.datasets[0].data = expenseValues;
  evolutionChart.data.datasets[1].data = balanceValues;
  evolutionChart.update();
}

function refreshHistoryInsights() {
  renderComparisonControls();
  renderEvolutionChart();
}

function updateSavedMonthsActive() {
  const selectedPeriod = getSelectedPeriod();

  savedMonthsList.querySelectorAll(".saved-month-button").forEach((button) => {
    const isActive =
      Number(button.dataset.month) === selectedPeriod.month &&
      Number(button.dataset.year) === selectedPeriod.year;

    button.classList.toggle("is-active", isActive);
  });
}

function renderSavedMonths(monthBudgets) {
  savedMonthsList.innerHTML = "";

  if (!monthBudgets.length) {
    savedMonthsEmpty.hidden = false;
    savedMonthsEmpty.textContent = "Nenhum mes salvo no banco ainda.";
    return;
  }

  savedMonthsEmpty.hidden = true;

  monthBudgets.forEach((budget) => {
    const item = document.createElement("li");
    const button = document.createElement("button");
    const periodRow = document.createElement("span");
    const period = document.createElement("span");
    const salary = document.createElement("span");
    const total = document.createElement("span");
    const balance = document.createElement("span");

    button.type = "button";
    button.className = "saved-month-button";
    button.dataset.month = budget.month;
    button.dataset.year = budget.year;
    button.classList.toggle("is-negative", budget.is_over_budget);
    button.setAttribute("aria-label", `Carregar orcamento de ${formatPeriod(budget.month, budget.year)}`);

    periodRow.className = "saved-month-period";
    period.textContent = formatPeriod(budget.month, budget.year);
    salary.textContent = currencyFormatter.format(budget.salary);

    total.className = "saved-month-total";
    total.textContent = `Gastos: ${currencyFormatter.format(budget.total_expenses)}`;

    balance.className = "saved-month-balance";
    balance.textContent = `Saldo: ${currencyFormatter.format(budget.remaining_balance)}`;

    periodRow.append(period, salary);
    button.append(periodRow, total, balance);
    button.addEventListener("click", async () => {
      hideFeedbackPopup();
      setSelectedPeriod(budget.month, budget.year);
      saveState();
      updateSavedMonthsActive();
      await loadBudgetFromDatabase();
    });

    item.appendChild(button);
    savedMonthsList.appendChild(item);
  });

  updateSavedMonthsActive();
}

function showSavedMonthsError() {
  const message = "Nao foi possivel carregar os meses salvos. Clique em Atualizar para tentar novamente.";

  savedMonthsList.innerHTML = "";
  savedMonthsEmpty.hidden = false;
  savedMonthsEmpty.textContent = message;
  showFeedbackPopup(message);
}

async function loadSavedMonths() {
  const originalButtonText = refreshSavedMonthsButton.textContent;
  refreshSavedMonthsButton.disabled = true;
  refreshSavedMonthsButton.textContent = "Atualizando...";

  try {
    const response = await fetch("/api/month-budgets");

    if (!response.ok) {
      showSavedMonthsError();
      return;
    }

    const data = await response.json();
    savedMonthBudgets = data.month_budgets || [];
    renderSavedMonths(savedMonthBudgets);
    refreshHistoryInsights();
    hideFeedbackPopup();
  } catch {
    showSavedMonthsError();
  } finally {
    refreshSavedMonthsButton.disabled = false;
    refreshSavedMonthsButton.textContent = originalButtonText;
  }
}

function categoryAppliesToExpenseType(category, expenseType) {
  return category.type === "both" || category.type === expenseType;
}

function renderCategoryOptions(datalist, expenseType) {
  datalist.innerHTML = "";

  categories
    .filter((category) => categoryAppliesToExpenseType(category, expenseType))
    .forEach((category) => {
      const option = document.createElement("option");
      option.value = category.name;
      datalist.appendChild(option);
    });
}

function renderCategories() {
  categoryList.innerHTML = "";
  renderCategoryOptions(fixedCategoryOptions, "fixed");
  renderCategoryOptions(variableCategoryOptions, "variable");

  if (!categories.length) {
    categoryStatus.textContent = "Categorias aparecem como sugestao nos gastos.";
    return;
  }

  categoryStatus.textContent = `${categories.length} categoria(s) cadastrada(s).`;

  categories.forEach((category) => {
    const item = document.createElement("li");
    const chip = document.createElement("span");
    const type = document.createElement("span");
    const actions = document.createElement("span");
    const editButton = document.createElement("button");
    const deleteButton = document.createElement("button");

    item.className = "category-item";

    chip.className = "category-chip";
    chip.textContent = category.name;
    type.textContent = categoryTypeLabels[category.type] || category.type;
    chip.appendChild(type);

    actions.className = "category-actions";

    editButton.type = "button";
    editButton.className = "category-action-button";
    editButton.textContent = "Editar";
    editButton.addEventListener("click", () => startEditingCategory(category));

    deleteButton.type = "button";
    deleteButton.className = "category-action-button is-danger";
    deleteButton.textContent = "Remover";
    deleteButton.addEventListener("click", () => deleteCategory(category));

    actions.append(editButton, deleteButton);
    item.append(chip, actions);
    categoryList.appendChild(item);
  });
}

function resetCategoryForm() {
  editingCategoryId = null;
  categoryNameInput.value = "";
  categoryTypeInput.value = "both";
  categorySubmitButton.textContent = "Adicionar";
  categoryCancelButton.hidden = true;
}

function startEditingCategory(category) {
  editingCategoryId = category.id;
  categoryNameInput.value = category.name;
  categoryTypeInput.value = category.type;
  categorySubmitButton.textContent = "Salvar";
  categoryCancelButton.hidden = false;
  categoryNameInput.focus();
  categoryStatus.textContent = `Editando ${category.name}.`;
}

async function loadCategories() {
  try {
    const response = await fetch("/api/categories");

    if (!response.ok) {
      categoryStatus.textContent = "Nao foi possivel carregar as categorias.";
      return;
    }

    const data = await response.json();
    categories = data.categories || [];
    renderCategories();
  } catch {
    categoryStatus.textContent = "Nao foi possivel carregar as categorias.";
  }
}

async function saveCategory(event) {
  event.preventDefault();

  const name = categoryNameInput.value.trim();
  const type = categoryTypeInput.value;

  if (!name) {
    categoryStatus.textContent = "Informe o nome da categoria.";
    return;
  }

  try {
    const url = editingCategoryId ? `/api/categories/${editingCategoryId}` : "/api/categories";
    const response = await fetch(url, {
      method: editingCategoryId ? "PATCH" : "POST",
      headers: jsonHeaders(true),
      body: JSON.stringify({ name, type }),
    });
    const data = await response.json();

    if (!response.ok) {
      categoryStatus.textContent = data.message || "Nao foi possivel salvar a categoria.";
      showFeedbackPopup(categoryStatus.textContent);
      return;
    }

    categoryStatus.textContent = editingCategoryId
      ? `Categoria ${data.category.name} atualizada.`
      : `Categoria ${data.category.name} adicionada.`;
    resetCategoryForm();
    await loadCategories();
  } catch {
    categoryStatus.textContent = "Nao foi possivel salvar a categoria.";
    showFeedbackPopup(categoryStatus.textContent);
  }
}

async function deleteCategory(category) {
  const shouldDelete = window.confirm(`Remover a categoria ${category.name}?`);

  if (!shouldDelete) {
    return;
  }

  try {
    const response = await fetch(`/api/categories/${category.id}`, {
      method: "DELETE",
      headers: jsonHeaders(true),
    });
    const data = await response.json();

    if (!response.ok) {
      categoryStatus.textContent = data.message || "Nao foi possivel remover a categoria.";
      showFeedbackPopup(categoryStatus.textContent);
      return;
    }

    categoryStatus.textContent = data.deleted ? "Categoria removida." : "Categoria nao encontrada.";
    await loadCategories();
  } catch {
    categoryStatus.textContent = "Nao foi possivel remover a categoria.";
    showFeedbackPopup(categoryStatus.textContent);
  }
}

function createExpenseRow(expense = {}, expenseType = "fixed") {
  const row = rowTemplate.content.firstElementChild.cloneNode(true);
  const descriptionInput = row.querySelector(".description-input");
  const categoryInput = row.querySelector(".category-input");
  const amountInput = row.querySelector(".amount-input");
  const descriptionLabel = row.querySelector(".description-label");
  const categoryLabel = row.querySelector(".category-label");
  const amountLabel = row.querySelector(".amount-label");
  const removeButton = row.querySelector(".remove-row");
  const rowId = rowCounter;

  rowCounter += 1;

  descriptionInput.value = expense.description || "";
  categoryInput.value = expense.category || "";
  amountInput.value = formatAmountForInput(expense.amount);
  categoryInput.setAttribute("list", expenseType === "variable" ? "variableCategoryOptions" : "fixedCategoryOptions");

  descriptionInput.id = `expenseDescription${rowId}`;
  categoryInput.id = `expenseCategory${rowId}`;
  amountInput.id = `expenseAmount${rowId}`;
  descriptionLabel.htmlFor = descriptionInput.id;
  categoryLabel.htmlFor = categoryInput.id;
  amountLabel.htmlFor = amountInput.id;

  descriptionInput.addEventListener("input", scheduleRefresh);
  categoryInput.addEventListener("input", scheduleRefresh);
  amountInput.addEventListener("input", handleMoneyInput);
  removeButton.addEventListener("click", () => {
    row.remove();
    ensureOneRow(fixedBody);
    ensureOneRow(variableBody);
    saveState();
    refreshSummary();
  });

  return row;
}

function addExpenseRow(tbody, expense = {}) {
  const expenseType = tbody === variableBody ? "variable" : "fixed";
  tbody.appendChild(createExpenseRow(expense, expenseType));
}

function ensureOneRow(tbody) {
  if (tbody.children.length === 0) {
    addExpenseRow(tbody);
  }
}

function collectExpenses(tbody) {
  return [...tbody.querySelectorAll("tr")].map((row) => ({
    description: row.querySelector(".description-input").value.trim(),
    category: row.querySelector(".category-input").value.trim(),
    amount: row.querySelector(".amount-input").value.trim(),
  }));
}

function sanitizeMoneyText(value) {
  let rawValue = String(value || "").trim();

  if (!rawValue.includes(",") && rawValue.includes(".")) {
    const parts = rawValue.split(".");

    if (parts.length === 2 && parts[1].length <= 2) {
      rawValue = rawValue.replace(".", ",");
    }
  }

  rawValue = rawValue.replace(/\./g, "");
  let nextValue = rawValue.replace(/[^\d,]/g, "");
  const commaIndex = nextValue.indexOf(",");

  if (commaIndex !== -1) {
    nextValue =
      nextValue.slice(0, commaIndex + 1) +
      nextValue.slice(commaIndex + 1).replace(/,/g, "").slice(0, 2);
  }

  return nextValue;
}

function formatAmountForInput(value) {
  if (value === undefined || value === null || value === "") {
    return "";
  }

  const numberValue = Number(String(value).replace(",", "."));

  if (Number.isNaN(numberValue)) {
    return sanitizeMoneyText(value);
  }

  return numberValue.toFixed(2).replace(".", ",");
}

function handleMoneyInput(event) {
  const sanitized = sanitizeMoneyText(event.target.value);

  if (event.target.value !== sanitized) {
    event.target.value = sanitized;
  }

  scheduleRefresh();
}

function getClientState() {
  return {
    salary: salaryInput.value.trim(),
    fixedExpenses: collectExpenses(fixedBody),
    variableExpenses: collectExpenses(variableBody),
    selectedPeriod: getSelectedPeriod(),
  };
}

function getPayload() {
  const state = getClientState();

  return {
    month: state.selectedPeriod.month,
    year: state.selectedPeriod.year,
    salary: state.salary,
    fixed_expenses: state.fixedExpenses,
    variable_expenses: state.variableExpenses,
  };
}

function saveState() {
  if (isRestoringState) {
    return;
  }

  localStorage.setItem(STORAGE_KEY, JSON.stringify(getClientState()));
}

function loadState() {
  try {
    return JSON.parse(localStorage.getItem(STORAGE_KEY));
  } catch {
    return null;
  }
}

function restoreState() {
  const savedState = loadState();
  const defaultPeriod = getDefaultPeriod();
  const savedPeriod = savedState?.selectedPeriod || {};

  isRestoringState = true;
  fixedBody.innerHTML = "";
  variableBody.innerHTML = "";
  setSelectedPeriod(savedPeriod.month || defaultPeriod.month, savedPeriod.year || defaultPeriod.year);

  if (savedState) {
    salaryInput.value = sanitizeMoneyText(savedState.salary);
    (savedState.fixedExpenses || []).forEach((expense) => addExpenseRow(fixedBody, expense));
    (savedState.variableExpenses || []).forEach((expense) => addExpenseRow(variableBody, expense));
  }

  ensureOneRow(fixedBody);
  ensureOneRow(variableBody);
  isRestoringState = false;
}

function resetState() {
  const shouldClear = window.confirm("Deseja apagar todos os dados salvos neste navegador?");

  if (!shouldClear) {
    return;
  }

  localStorage.removeItem(STORAGE_KEY);
  salaryInput.value = "";
  fixedBody.innerHTML = "";
  variableBody.innerHTML = "";
  addExpenseRow(fixedBody);
  addExpenseRow(variableBody);
  refreshSummary();
}

function clearBudgetForm() {
  isRestoringState = true;
  salaryInput.value = "";
  fixedBody.innerHTML = "";
  variableBody.innerHTML = "";
  addExpenseRow(fixedBody);
  addExpenseRow(variableBody);
  isRestoringState = false;
}

function replaceRows(tbody, expenses) {
  tbody.innerHTML = "";
  (expenses || []).forEach((expense) => addExpenseRow(tbody, expense));
  ensureOneRow(tbody);
}

async function saveBudgetToDatabase() {
  saveState();
  hideFeedbackPopup();

  const selectedPeriod = getSelectedPeriod();
  const originalButtonText = saveBudgetButton.textContent;
  saveBudgetButton.disabled = true;
  saveBudgetButton.textContent = "Salvando...";
  statusMessage.classList.remove("is-negative");
  statusMessage.textContent = `Salvando dados no banco para ${formatPeriod(selectedPeriod.month, selectedPeriod.year)}...`;

  try {
    const response = await fetch("/api/month-budget", {
      method: "POST",
      headers: jsonHeaders(true),
      body: JSON.stringify(getPayload()),
    });

    if (!response.ok) {
      statusMessage.textContent = "Nao foi possivel salvar no banco de dados.";
      statusMessage.classList.add("is-negative");
      return;
    }

    const data = await response.json();
    statusMessage.classList.remove("is-negative");
    statusMessage.textContent = `Dados salvos no banco para ${formatPeriod(data.month, data.year)}.`;
    hideFeedbackPopup();
    await loadSavedMonths();
  } catch {
    statusMessage.textContent = "Nao foi possivel salvar no banco de dados.";
    statusMessage.classList.add("is-negative");
  } finally {
    saveBudgetButton.disabled = false;
    saveBudgetButton.textContent = originalButtonText;
  }
}

async function loadBudgetFromDatabase(options = {}) {
  const { silentMissing = false } = options;
  const selectedPeriod = getSelectedPeriod();
  const params = new URLSearchParams({
    month: selectedPeriod.month,
    year: selectedPeriod.year,
  });
  statusMessage.classList.remove("is-negative");
  statusMessage.textContent = `Buscando dados no banco para ${formatPeriod(selectedPeriod.month, selectedPeriod.year)}...`;

  try {
    const response = await fetch(`/api/month-budget?${params.toString()}`);

    if (!response.ok) {
      statusMessage.textContent = "Nao foi possivel carregar os dados do banco.";
      statusMessage.classList.add("is-negative");
      showFeedbackPopup("Nao foi possivel carregar os dados do banco.");
      return;
    }

    const data = await response.json();

    if (!data.found) {
      if (silentMissing) {
        clearBudgetForm();
        saveState();
        await refreshSummary();
        statusMessage.classList.remove("is-negative");
        statusMessage.textContent = `Nenhum dado salvo para ${formatPeriod(data.month, data.year)}. Tela pronta para um novo orcamento.`;
        hideFeedbackPopup();
        updateSavedMonthsActive();
        return;
      }

      const notFoundMessage = `Nenhum dado salvo para ${formatPeriod(data.month, data.year)}. Escolha outro mes/ano ou salve este periodo primeiro.`;
      statusMessage.classList.add("is-negative");
      statusMessage.textContent = notFoundMessage;
      showFeedbackPopup(notFoundMessage);
      return;
    }

    isRestoringState = true;
    salaryInput.value = formatAmountForInput(data.salary);
    replaceRows(fixedBody, data.fixed_expenses);
    replaceRows(variableBody, data.variable_expenses);
    isRestoringState = false;

    saveState();
    await refreshSummary();
    statusMessage.classList.remove("is-negative");
    statusMessage.textContent = `Dados carregados do banco para ${formatPeriod(data.month, data.year)}.`;
    hideFeedbackPopup();
    updateSavedMonthsActive();
  } catch {
    statusMessage.textContent = "Nao foi possivel carregar os dados do banco.";
    statusMessage.classList.add("is-negative");
    showFeedbackPopup("Nao foi possivel carregar os dados do banco.");
  } finally {
  }
}

async function duplicatePreviousMonth() {
  const targetPeriod = getSelectedPeriod();
  const sourcePeriod = getPreviousPeriod(targetPeriod);
  const shouldDuplicate = window.confirm(
    `Copiar os dados de ${formatPeriod(sourcePeriod.month, sourcePeriod.year)} para ${formatPeriod(targetPeriod.month, targetPeriod.year)}?`
  );

  if (!shouldDuplicate) {
    return;
  }

  const params = new URLSearchParams({
    month: sourcePeriod.month,
    year: sourcePeriod.year,
  });
  const originalButtonText = duplicatePreviousButton.textContent;
  duplicatePreviousButton.disabled = true;
  duplicatePreviousButton.textContent = "Duplicando...";
  hideFeedbackPopup();
  statusMessage.classList.remove("is-negative");
  statusMessage.textContent = `Buscando dados de ${formatPeriod(sourcePeriod.month, sourcePeriod.year)}...`;

  try {
    const response = await fetch(`/api/month-budget?${params.toString()}`);

    if (!response.ok) {
      statusMessage.textContent = "Nao foi possivel duplicar o mes anterior.";
      statusMessage.classList.add("is-negative");
      showFeedbackPopup("Nao foi possivel duplicar o mes anterior.");
      return;
    }

    const data = await response.json();

    if (!data.found) {
      const notFoundMessage = `Nenhum dado salvo para ${formatPeriod(sourcePeriod.month, sourcePeriod.year)}. Salve o mes anterior antes de duplicar.`;
      statusMessage.classList.add("is-negative");
      statusMessage.textContent = notFoundMessage;
      showFeedbackPopup(notFoundMessage);
      return;
    }

    isRestoringState = true;
    salaryInput.value = formatAmountForInput(data.salary);
    replaceRows(fixedBody, data.fixed_expenses);
    replaceRows(variableBody, data.variable_expenses);
    isRestoringState = false;

    setSelectedPeriod(targetPeriod.month, targetPeriod.year);
    saveState();
    await refreshSummary();
    updateSavedMonthsActive();
    statusMessage.classList.remove("is-negative");
    statusMessage.textContent = `Dados copiados de ${formatPeriod(sourcePeriod.month, sourcePeriod.year)} para ${formatPeriod(targetPeriod.month, targetPeriod.year)}. Revise e clique em Salvar.`;
  } catch {
    statusMessage.textContent = "Nao foi possivel duplicar o mes anterior.";
    statusMessage.classList.add("is-negative");
    showFeedbackPopup("Nao foi possivel duplicar o mes anterior.");
  } finally {
    duplicatePreviousButton.disabled = false;
    duplicatePreviousButton.textContent = originalButtonText;
  }
}

function scheduleLoadSelectedPeriod() {
  if (isRestoringState) {
    return;
  }

  window.clearTimeout(periodChangeTimer);
  periodChangeTimer = window.setTimeout(() => {
    loadBudgetFromDatabase({ silentMissing: true });
  }, 250);
}

function validateRows() {
  const rows = [...fixedBody.querySelectorAll("tr"), ...variableBody.querySelectorAll("tr")];
  let hasIncompleteRow = false;

  rows.forEach((row) => {
    const description = row.querySelector(".description-input").value.trim();
    const category = row.querySelector(".category-input").value.trim();
    const amountInput = row.querySelector(".amount-input");
    const amount = amountInput.value.trim();
    const hasText = Boolean(description || category);
    const isIncomplete = hasText && !amount;

    amountInput.classList.toggle("is-invalid", isIncomplete);
    hasIncompleteRow = hasIncompleteRow || isIncomplete;
  });

  return hasIncompleteRow;
}

function scheduleRefresh() {
  window.clearTimeout(refreshTimer);
  saveState();
  refreshTimer = window.setTimeout(refreshSummary, 120);
}

async function refreshSummary() {
  saveState();

  const response = await fetch("/api/summary", {
    method: "POST",
    headers: jsonHeaders(),
    body: JSON.stringify(getPayload()),
  });

  if (!response.ok) {
    statusMessage.textContent = "Nao foi possivel recalcular os valores.";
    statusMessage.classList.add("is-negative");
    return;
  }

  const summary = await response.json();
  renderSummary(summary);
  renderChart(summary.chart);
}

function renderSummary(summary) {
  const hasIncompleteRow = validateRows();

  summaryFields.salary.textContent = currencyFormatter.format(summary.salary);
  summaryFields.fixed.textContent = currencyFormatter.format(summary.fixed_total);
  summaryFields.variable.textContent = currencyFormatter.format(summary.variable_total);
  summaryFields.total.textContent = currencyFormatter.format(summary.total_expenses);
  summaryFields.balance.textContent = currencyFormatter.format(summary.remaining_balance);
  summaryFields.committed.textContent = `${percentFormatter.format(summary.committed_percentage)}%`;
  summaryFields.available.textContent = `${percentFormatter.format(summary.available_percentage)}%`;

  balanceRow.classList.toggle("is-negative", summary.is_over_budget);
  statusMessage.classList.toggle("is-negative", summary.is_over_budget);

  if (hasIncompleteRow) {
    salaryHint.textContent = "O salario informado esta sendo usado como base dos calculos.";
    statusMessage.textContent = "Ha linhas com descricao ou categoria sem valor informado.";
  } else if (!summary.has_salary) {
    salaryHint.textContent = "Informe o salario para calcular os percentuais.";
    statusMessage.textContent = "Preencha o salario mensal para iniciar o acompanhamento.";
  } else if (summary.is_over_budget) {
    salaryHint.textContent = "O salario informado esta sendo usado como base dos calculos.";
    statusMessage.textContent = "Atencao: os gastos ultrapassaram o salario mensal.";
  } else if (summary.total_expenses === 0) {
    salaryHint.textContent = "O salario informado esta sendo usado como base dos calculos.";
    statusMessage.textContent = "Adicione gastos fixos ou variados para montar a distribuicao.";
  } else {
    salaryHint.textContent = "O salario informado esta sendo usado como base dos calculos.";
    statusMessage.textContent = "Resumo atualizado com os dados informados e salvo neste navegador.";
  }
}

function renderChart(chartData) {
  const hasChartData = chartData.values.some((value) => value > 0);
  chartEmpty.classList.toggle("is-hidden", hasChartData);
  renderChartLegend(chartData);

  if (!window.Chart) {
    return;
  }

  if (!financeChart) {
    financeChart = new Chart(chartCanvas, {
      type: "pie",
      data: {
        labels: chartData.labels,
        datasets: [
          {
            data: chartData.values,
            backgroundColor: chartColors,
            borderColor: "#ffffff",
            borderWidth: 3,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            display: false,
          },
          tooltip: {
            callbacks: {
              label: (context) => {
                const label = context.label || "";
                const value = currencyFormatter.format(context.parsed || 0);
                return `${label}: ${value}`;
              },
            },
          },
        },
      },
    });
    return;
  }

  financeChart.data.labels = chartData.labels;
  financeChart.data.datasets[0].data = chartData.values;
  financeChart.update();
}

function renderChartLegend(chartData) {
  const total = chartData.values.reduce((sum, value) => sum + value, 0);

  chartLegend.innerHTML = chartData.labels
    .map((label, index) => {
      const value = chartData.values[index] || 0;
      const percent = total > 0 ? (value / total) * 100 : 0;

      return `
        <li>
          <span class="legend-swatch" style="background-color: ${chartColors[index]}"></span>
          <span>
            <span class="legend-label">${label}</span>
            <span class="legend-value">${currencyFormatter.format(value)} - ${percentFormatter.format(percent)}%</span>
          </span>
        </li>
      `;
    })
    .join("");
}

document.querySelectorAll(".add-row").forEach((button) => {
  button.addEventListener("click", () => {
    const targetBody = document.querySelector(`#${button.dataset.target}`);
    addExpenseRow(targetBody);
    saveState();
    refreshSummary();
  });
});

salaryInput.addEventListener("input", handleMoneyInput);
clearDataButton.addEventListener("click", resetState);
saveBudgetButton.addEventListener("click", saveBudgetToDatabase);
duplicatePreviousButton.addEventListener("click", duplicatePreviousMonth);
feedbackPopupClose.addEventListener("click", hideFeedbackPopup);
refreshSavedMonthsButton.addEventListener("click", loadSavedMonths);
compareBaseMonth.addEventListener("change", renderComparison);
compareTargetMonth.addEventListener("change", renderComparison);
categoryForm.addEventListener("submit", saveCategory);
categoryCancelButton.addEventListener("click", () => {
  resetCategoryForm();
  categoryStatus.textContent = `${categories.length} categoria(s) cadastrada(s).`;
});
periodMonthInput.addEventListener("change", () => {
  hideFeedbackPopup();
  updatePeriodLabel();
  updateSavedMonthsActive();
  saveState();
  scheduleLoadSelectedPeriod();
});
periodYearInput.addEventListener("input", () => {
  hideFeedbackPopup();
  updatePeriodLabel();
  updateSavedMonthsActive();
  saveState();
  scheduleLoadSelectedPeriod();
});

restoreState();
refreshSummary();
loadSavedMonths();
loadCategories();
