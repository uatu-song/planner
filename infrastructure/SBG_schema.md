# Standards-Based Grading App Schema & Implementation Plan
## PSCA 8th Grade ELA

---

## 1. Database Schema

### Core Tables

#### `standards`
```sql
CREATE TABLE standards (
  id INTEGER PRIMARY KEY,
  code VARCHAR(20) UNIQUE NOT NULL, -- e.g., "RL.8.1", "W.8.1a"
  category VARCHAR(10) NOT NULL, -- "RL", "RI", "W", "SL", "L"
  description TEXT NOT NULL,
  measurement_topic INTEGER, -- MT1-5 mapping
  grade_level INTEGER DEFAULT 8,
  is_ninth_grade BOOLEAN DEFAULT FALSE, -- for 8/9 accelerated tracking
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### `measurement_topics`
```sql
CREATE TABLE measurement_topics (
  id INTEGER PRIMARY KEY,
  code VARCHAR(10) NOT NULL, -- "MT1", "MT2", etc.
  name VARCHAR(100) NOT NULL,
  description TEXT,
  weight DECIMAL(3,2) DEFAULT 1.0 -- for weighted grading if needed
);
```

#### `students`
```sql
CREATE TABLE students (
  id INTEGER PRIMARY KEY,
  student_id VARCHAR(50) UNIQUE NOT NULL,
  first_name VARCHAR(100) NOT NULL,
  last_name VARCHAR(100) NOT NULL,
  email VARCHAR(255),
  parent_email VARCHAR(255),
  course VARCHAR(50) NOT NULL, -- "Gen Ed 8th ELA" or "ELA 8/9"
  period INTEGER,
  is_active BOOLEAN DEFAULT TRUE,
  notes TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### `units`
```sql
CREATE TABLE units (
  id INTEGER PRIMARY KEY,
  unit_number INTEGER NOT NULL,
  title VARCHAR(200) NOT NULL,
  text_focus VARCHAR(200), -- e.g., "Short Stories", "Chew On This"
  weeks VARCHAR(50), -- e.g., "1-3", "4-11"
  essential_question TEXT,
  unit_type VARCHAR(50), -- "Literature Seminar" or "Writing"
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### `assignments`
```sql
CREATE TABLE assignments (
  id INTEGER PRIMARY KEY,
  unit_id INTEGER REFERENCES units(id),
  name VARCHAR(200) NOT NULL,
  type VARCHAR(50) NOT NULL, -- "Formative", "Summative", "Discussion", "Writing Process", "On-Demand"
  category VARCHAR(50), -- "Constructed Response", "Argument", "Historical Narrative", etc.
  lesson_number INTEGER,
  week_number INTEGER,
  description TEXT,
  points_possible INTEGER DEFAULT 100,
  is_retakeable BOOLEAN DEFAULT TRUE,
  max_retakes INTEGER DEFAULT 2,
  date_assigned DATE,
  date_due DATE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### `assignment_standards`
```sql
CREATE TABLE assignment_standards (
  id INTEGER PRIMARY KEY,
  assignment_id INTEGER REFERENCES assignments(id),
  standard_id INTEGER REFERENCES standards(id),
  is_primary BOOLEAN DEFAULT FALSE, -- Primary vs Additional standards
  weight DECIMAL(3,2) DEFAULT 1.0
);
```

#### `grades`
```sql
CREATE TABLE grades (
  id INTEGER PRIMARY KEY,
  student_id INTEGER REFERENCES students(id),
  assignment_id INTEGER REFERENCES assignments(id),
  standard_id INTEGER REFERENCES standards(id),
  proficiency_level INTEGER CHECK (proficiency_level IN (1,2,3,4)),
  -- 1=Beginning, 2=Developing, 3=Proficient, 4=Advanced
  raw_score DECIMAL(5,2),
  percentage DECIMAL(5,2),
  attempt_number INTEGER DEFAULT 1,
  is_current_best BOOLEAN DEFAULT TRUE, -- For tracking mastery
  evidence_type VARCHAR(50), -- "Assignment", "Conference", "Observation", "Retake"
  evidence_notes TEXT,
  date_assessed DATE,
  entered_by VARCHAR(100),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### `student_standard_mastery`
```sql
CREATE TABLE student_standard_mastery (
  id INTEGER PRIMARY KEY,
  student_id INTEGER REFERENCES students(id),
  standard_id INTEGER REFERENCES standards(id),
  current_proficiency INTEGER CHECK (current_proficiency IN (1,2,3,4)),
  highest_proficiency INTEGER CHECK (highest_proficiency IN (1,2,3,4)),
  attempts_count INTEGER DEFAULT 0,
  last_assessed DATE,
  trend VARCHAR(20), -- "improving", "declining", "stable", "new"
  mastery_date DATE, -- When they first hit proficiency (3+)
  notes TEXT,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### `retakes`
```sql
CREATE TABLE retakes (
  id INTEGER PRIMARY KEY,
  student_id INTEGER REFERENCES students(id),
  assignment_id INTEGER REFERENCES assignments(id),
  standard_id INTEGER REFERENCES standards(id),
  request_date DATE,
  scheduled_date DATE,
  completed_date DATE,
  status VARCHAR(50), -- "requested", "scheduled", "completed", "cancelled"
  preparation_evidence TEXT, -- What they did to prepare
  teacher_notes TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### `parent_conferences`
```sql
CREATE TABLE parent_conferences (
  id INTEGER PRIMARY KEY,
  student_id INTEGER REFERENCES students(id),
  conference_date DATE,
  attendees TEXT,
  strengths TEXT,
  areas_for_growth TEXT,
  action_plan TEXT,
  follow_up_date DATE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### `progress_reports`
```sql
CREATE TABLE progress_reports (
  id INTEGER PRIMARY KEY,
  student_id INTEGER REFERENCES students(id),
  report_date DATE,
  report_type VARCHAR(50), -- "Weekly", "Unit", "Quarter", "Semester"
  overall_proficiency DECIMAL(3,2),
  mt1_proficiency DECIMAL(3,2), -- Information & Ideas
  mt2_proficiency DECIMAL(3,2), -- Author's Craft
  mt3_proficiency DECIMAL(3,2), -- Writing
  mt4_proficiency DECIMAL(3,2), -- Speaking & Listening
  mt5_proficiency DECIMAL(3,2), -- Language
  strengths TEXT,
  areas_for_growth TEXT,
  parent_comments TEXT,
  teacher_comments TEXT,
  generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 2. Pre-Populated Data Structure

### Standards Mapping (Based on Your Curriculum)

```javascript
const MEASUREMENT_TOPICS = {
  MT1: "Information & Ideas (Comprehension, Inference, Analysis)",
  MT2: "Author's Craft (Literary Devices, Structure, Purpose)",
  MT3: "Writing (Various Genres)",
  MT4: "Speaking & Listening (Discussion, Presentation)",
  MT5: "Language (Grammar, Vocabulary, Conventions)"
};

const STANDARDS_MAP = {
  // Reading Literature
  "RL.8.1": { mt: 1, desc: "Cite textual evidence to support analysis" },
  "RL.8.2": { mt: 1, desc: "Determine theme and analyze development" },
  "RL.8.3": { mt: 2, desc: "Analyze dialogue/incidents revealing character" },
  "RL.8.4": { mt: 2, desc: "Determine meaning of words/phrases" },
  "RL.8.5": { mt: 2, desc: "Compare/contrast text structures" },
  "RL.8.6": { mt: 2, desc: "Analyze POV differences" },
  "RL.8.7": { mt: 2, desc: "Analyze multimedia elements" },
  "RL.8.8": { mt: 1, desc: "Delineate/evaluate arguments" },
  "RL.8.9": { mt: 1, desc: "Analyze modern fiction/traditional themes" },
  
  // Reading Informational
  "RI.8.1": { mt: 1, desc: "Cite textual evidence" },
  "RI.8.2": { mt: 1, desc: "Determine central idea" },
  "RI.8.3": { mt: 1, desc: "Analyze text connections" },
  "RI.8.4": { mt: 2, desc: "Determine word meanings" },
  "RI.8.5": { mt: 2, desc: "Analyze paragraph structure" },
  "RI.8.6": { mt: 2, desc: "Determine author's POV" },
  "RI.8.7": { mt: 2, desc: "Evaluate different mediums" },
  "RI.8.8": { mt: 1, desc: "Evaluate argument and claims" },
  "RI.8.9": { mt: 1, desc: "Analyze conflicting information" },
  
  // Writing
  "W.8.1": { mt: 3, desc: "Write arguments" },
  "W.8.1a": { mt: 3, desc: "Introduce claims" },
  "W.8.1b": { mt: 3, desc: "Support claims with reasoning" },
  "W.8.2": { mt: 3, desc: "Write informative texts" },
  "W.8.2a": { mt: 3, desc: "Introduce topic clearly" },
  "W.8.2b": { mt: 3, desc: "Develop topic with facts" },
  "W.8.2c": { mt: 3, desc: "Use transitions" },
  "W.8.2d": { mt: 3, desc: "Use precise language" },
  "W.8.3": { mt: 3, desc: "Write narratives" },
  "W.8.3a": { mt: 3, desc: "Engage reader with context" },
  "W.8.3b": { mt: 3, desc: "Use narrative techniques" },
  "W.8.3c": { mt: 3, desc: "Use transition words" },
  "W.8.3d": { mt: 3, desc: "Use precise words/sensory language" },
  "W.8.4": { mt: 3, desc: "Produce clear writing" },
  "W.8.5": { mt: 3, desc: "Develop/strengthen writing" },
  "W.8.6": { mt: 3, desc: "Use technology to produce writing" },
  "W.8.7": { mt: 3, desc: "Conduct research projects" },
  "W.8.8": { mt: 3, desc: "Gather relevant information" },
  "W.8.9": { mt: 3, desc: "Draw evidence from texts" },
  "W.8.10": { mt: 3, desc: "Write routinely" },
  
  // Speaking & Listening
  "SL.8.1": { mt: 4, desc: "Engage in collaborative discussions" },
  "SL.8.1a": { mt: 4, desc: "Come to discussions prepared" },
  "SL.8.1b": { mt: 4, desc: "Follow rules for discussions" },
  "SL.8.1c": { mt: 4, desc: "Pose questions connecting ideas" },
  "SL.8.1d": { mt: 4, desc: "Acknowledge new information" },
  "SL.8.2": { mt: 4, desc: "Analyze purpose of information" },
  "SL.8.3": { mt: 4, desc: "Delineate speaker's argument" },
  "SL.8.4": { mt: 4, desc: "Present claims and findings" },
  "SL.8.5": { mt: 4, desc: "Integrate multimedia" },
  "SL.8.6": { mt: 4, desc: "Adapt speech to context" },
  
  // Language
  "L.8.1": { mt: 5, desc: "Demonstrate command of grammar" },
  "L.8.1a": { mt: 5, desc: "Explain verbals" },
  "L.8.1b": { mt: 5, desc: "Form/use active and passive voice" },
  "L.8.1c": { mt: 5, desc: "Form/use verb moods" },
  "L.8.1d": { mt: 5, desc: "Recognize shifts in voice/mood" },
  "L.8.2": { mt: 5, desc: "Demonstrate command of conventions" },
  "L.8.2a": { mt: 5, desc: "Use punctuation for pause/break" },
  "L.8.2b": { mt: 5, desc: "Use ellipsis for omission" },
  "L.8.3": { mt: 5, desc: "Use knowledge of language" },
  "L.8.4": { mt: 5, desc: "Determine word meanings" },
  "L.8.5": { mt: 5, desc: "Demonstrate understanding of figurative language" },
  "L.8.6": { mt: 5, desc: "Acquire academic vocabulary" }
};
```

### Unit-Specific Assignments Structure

```javascript
const UNITS = [
  {
    number: 1,
    title: "Short Stories",
    weeks: "1-3",
    type: "both", // Has both Literature and Writing components
    literature: {
      primaryStandards: ["RL.8.1", "RL.8.2", "RL.8.3", "RL.8.6"],
      texts: ["The Dinner Party", "The Monkey's Paw", "Charles"],
      assignments: [
        { name: "Citing Evidence Practice", type: "Formative", standards: ["RL.8.1"] },
        { name: "Plot Development Analysis", type: "Formative", standards: ["RL.8.3"] },
        { name: "Character Development Essay", type: "Summative", standards: ["RL.8.3", "W.8.9"] },
        { name: "Short Story Unit Test", type: "Summative", standards: ["RL.8.1", "RL.8.2", "RL.8.3", "RL.8.6"] }
      ]
    },
    writing: {
      primaryStandards: ["W.8.4", "W.8.9", "L.8.1"],
      focus: "Constructed Response Writing",
      assignments: [
        { name: "RACE Strategy Practice", type: "Formative", standards: ["W.8.4"] },
        { name: "Text Evidence Integration", type: "Formative", standards: ["W.8.9"] },
        { name: "Constructed Response Assessment", type: "Summative", standards: ["W.8.4", "W.8.9", "L.8.1"] }
      ]
    }
  },
  {
    number: 2,
    title: "Chew On This",
    weeks: "4-11",
    type: "both",
    literature: {
      primaryStandards: ["RI.8.6", "RI.8.8"],
      additionalStandards: ["RL.8.1", "RI.8.1", "RI.8.2", "RI.8.4", "RI.8.7", "RI.8.9", "RL.8.2", "L.8.4", "L.8.5", "L.8.6", "SL.8.2", "SL.8.3"],
      texts: ["Chew On This (excerpts)"],
      assignments: [
        { name: "Author's Purpose Analysis", type: "Formative", standards: ["RI.8.6"] },
        { name: "Evaluating Arguments Worksheet", type: "Formative", standards: ["RI.8.8"] },
        { name: "Fast Food Industry Research", type: "Formative", standards: ["RI.8.1", "RI.8.7"] },
        { name: "Argument Analysis Essay", type: "Summative", standards: ["RI.8.6", "RI.8.8", "W.8.1"] },
        { name: "Socratic Seminar", type: "Discussion", standards: ["SL.8.1", "SL.8.3"] }
      ]
    },
    writing: {
      primaryStandards: ["W.8.1", "W.8.1a", "W.8.1b", "L.8.1", "L.8.1a"],
      focus: "Argument Writing",
      assignments: [
        { name: "Claim Development", type: "Formative", standards: ["W.8.1a"] },
        { name: "Evidence and Reasoning", type: "Formative", standards: ["W.8.1b"] },
        { name: "Counterclaim Practice", type: "Formative", standards: ["W.8.1a"] },
        { name: "Editorial Draft", type: "Process", standards: ["W.8.1", "W.8.5"] },
        { name: "Final Editorial", type: "Summative", standards: ["W.8.1", "W.8.1a", "W.8.1b", "L.8.1"] },
        { name: "Video Essay", type: "Summative", standards: ["W.8.1", "W.8.6", "SL.8.5"] }
      ]
    }
  },
  {
    number: 3,
    title: "Chains",
    weeks: "12-17",
    type: "both",
    literature: {
      primaryStandards: ["RL.8.2", "RL.8.3", "RL.8.6"],
      additionalStandards: ["RL.8.1", "RI.8.1", "RL.8.4", "RL.8.5", "RI.8.2", "RI.8.6", "RI.8.7", "RI.8.9", "L.8.4", "L.8.5", "L.8.6", "SL.8.2"],
      texts: ["Chains by Laurie Halse Anderson"],
      assignments: [
        { name: "Historical Context Research", type: "Formative", standards: ["RI.8.1", "RI.8.7"] },
        { name: "Character Perspective Tracker", type: "Formative", standards: ["RL.8.3", "RL.8.6"] },
        { name: "Theme Development Essay", type: "Summative", standards: ["RL.8.2", "W.8.9"] },
        { name: "Chapter Quizzes", type: "Formative", standards: ["RL.8.1", "RL.8.2"] },
        { name: "Unit Test", type: "Summative", standards: ["RL.8.2", "RL.8.3", "RL.8.6"] }
      ]
    },
    writing: {
      primaryStandards: ["W.8.3", "W.8.3a", "W.8.3b", "W.8.3c", "W.8.3d", "L.8.1b", "L.8.1d", "L.8.2b"],
      focus: "Historical Narrative",
      assignments: [
        { name: "Setting Description", type: "Formative", standards: ["W.8.3a", "W.8.3d"] },
        { name: "Dialogue Writing", type: "Formative", standards: ["W.8.3b", "L.8.2b"] },
        { name: "Historical Narrative Draft", type: "Process", standards: ["W.8.3", "W.8.5"] },
        { name: "Peer Review", type: "Formative", standards: ["W.8.5"] },
        { name: "Final Historical Narrative", type: "Summative", standards: ["W.8.3", "L.8.1b", "L.8.1d"] }
      ]
    }
  },
  {
    number: 4,
    title: "Frederick Douglass",
    weeks: "19-23",
    type: "both",
    literature: {
      primaryStandards: ["RI.8.2", "RI.8.3", "RI.8.4", "RI.8.5"],
      additionalStandards: ["RL.8.1", "RI.8.1", "RI.8.6", "RL.8.2", "RL.8.4", "L.8.4", "L.8.5", "L.8.6", "SL.8.2", "SL.8.3"],
      texts: ["Narrative of the Life of Frederick Douglass (excerpts)"],
      assignments: [
        { name: "Central Idea Tracking", type: "Formative", standards: ["RI.8.2"] },
        { name: "Text Structure Analysis", type: "Formative", standards: ["RI.8.5"] },
        { name: "Vocabulary in Context", type: "Formative", standards: ["RI.8.4", "L.8.4"] },
        { name: "Rhetorical Analysis Essay", type: "Summative", standards: ["RI.8.2", "RI.8.3", "RI.8.6"] },
        { name: "Socratic Seminar", type: "Discussion", standards: ["SL.8.1", "SL.8.3"] }
      ]
    },
    writing: {
      primaryStandards: ["W.8.2", "W.8.2a", "W.8.2b", "W.8.2c", "W.8.2d", "L.8.1c"],
      focus: "Informational/Research",
      assignments: [
        { name: "Research Question Development", type: "Formative", standards: ["W.8.7"] },
        { name: "Source Evaluation", type: "Formative", standards: ["W.8.8"] },
        { name: "Outline and Organization", type: "Formative", standards: ["W.8.2a"] },
        { name: "Research Paper Draft", type: "Process", standards: ["W.8.2", "W.8.5"] },
        { name: "Works Cited", type: "Formative", standards: ["W.8.8"] },
        { name: "Final Research Paper", type: "Summative", standards: ["W.8.2", "W.8.7", "W.8.8", "L.8.1c"] }
      ]
    }
  },
  {
    number: 5,
    title: "Animal Farm",
    weeks: "24-29",
    type: "both",
    literature: {
      primaryStandards: ["RL.8.2", "RL.8.3", "RL.8.9"],
      additionalStandards: ["RL.8.1", "RI.8.1", "RL.8.4", "RL.8.5", "RI.8.2", "L.8.4", "L.8.5", "L.8.6", "SL.8.2"],
      texts: ["Animal Farm by George Orwell"],
      assignments: [
        { name: "Allegory Identification", type: "Formative", standards: ["RL.8.9"] },
        { name: "Character Analysis Tracker", type: "Formative", standards: ["RL.8.3"] },
        { name: "Propaganda Techniques", type: "Formative", standards: ["RL.8.4", "L.8.5"] },
        { name: "Theme Analysis Essay", type: "Summative", standards: ["RL.8.2", "RL.8.9"] },
        { name: "Unit Test", type: "Summative", standards: ["RL.8.2", "RL.8.3", "RL.8.9"] }
      ]
    },
    writing: {
      primaryStandards: ["W.8.3", "W.8.3b", "W.8.3d", "L.8.1c", "L.8.1d", "L.8.2a", "L.8.3", "SL.8.2"],
      focus: "Narrative Satire",
      assignments: [
        { name: "Satire Techniques Study", type: "Formative", standards: ["L.8.3"] },
        { name: "Satirical Scene Draft", type: "Process", standards: ["W.8.3", "W.8.5"] },
        { name: "Peer Workshop", type: "Formative", standards: ["W.8.5", "SL.8.1"] },
        { name: "Final Satirical Narrative", type: "Summative", standards: ["W.8.3", "L.8.3"] }
      ]
    }
  },
  {
    number: 6,
    title: "A Midsummer Night's Dream",
    weeks: "30-33",
    type: "both",
    literature: {
      primaryStandards: ["RL.8.2", "RL.8.4", "RL.8.5"],
      additionalStandards: ["RL.8.1", "RI.8.1", "RI.8.2", "RI.8.6", "RL.8.3", "RL.8.6", "RL.8.7", "L.8.4", "L.8.5", "L.8.6"],
      texts: ["A Midsummer Night's Dream by William Shakespeare"],
      assignments: [
        { name: "Shakespearean Language Guide", type: "Formative", standards: ["RL.8.4", "L.8.4"] },
        { name: "Scene Analysis", type: "Formative", standards: ["RL.8.5"] },
        { name: "Character Relationships Map", type: "Formative", standards: ["RL.8.3"] },
        { name: "Performance Assessment", type: "Performance", standards: ["RL.8.7", "SL.8.6"] },
        { name: "Final Essay", type: "Summative", standards: ["RL.8.2", "RL.8.4", "RL.8.5"] }
      ]
    },
    writing: {
      primaryStandards: ["W.8.3d", "W.8.4", "L.8.1"],
      focus: "Narrative Poetry",
      assignments: [
        { name: "Poetic Devices Practice", type: "Formative", standards: ["L.8.5"] },
        { name: "Original Poem Draft", type: "Process", standards: ["W.8.3d", "W.8.5"] },
        { name: "Poetry Workshop", type: "Formative", standards: ["W.8.5", "SL.8.1"] },
        { name: "Poetry Portfolio", type: "Summative", standards: ["W.8.3d", "W.8.4", "L.8.1"] }
      ]
    }
  }
];
```

---

## 3. Key Features Implementation

### A. Standards Mastery Tracking
```javascript
// Algorithm for calculating current mastery
function calculateMastery(grades) {
  // SBG Philosophy: Show highest achievement, not average
  const sortedGrades = grades.sort((a, b) => b.proficiency_level - a.proficiency_level);
  
  // Consider most recent high scores (last 3 attempts)
  const recentHighs = sortedGrades.slice(0, 3);
  
  // Weight recent performance more heavily
  const weights = [0.5, 0.3, 0.2];
  let weightedScore = 0;
  
  recentHighs.forEach((grade, index) => {
    weightedScore += grade.proficiency_level * (weights[index] || 0);
  });
  
  return Math.round(weightedScore);
}
```

### B. Retake Management System
```javascript
const retakeRules = {
  maxRetakes: 2,
  preparationRequired: true,
  waitPeriod: 3, // days
  requirements: [
    "Complete practice problems",
    "Attend tutoring or conference",
    "Submit reflection on areas for improvement"
  ]
};
```

### C. Progress Visualization Components
- **Standards Progress Grid**: Visual heat map showing proficiency per standard
- **Growth Over Time Chart**: Line graph showing improvement trajectory
- **Measurement Topic Dashboard**: Pie charts for MT1-5 distribution
- **Unit Progression Tracker**: Shows completion and mastery by unit

### D. Parent Communication Features
```javascript
const parentReportTemplate = {
  header: "Standards-Based Progress Report",
  sections: [
    {
      title: "Current Mastery Levels",
      content: "standardsMasteryGrid"
    },
    {
      title: "Recent Achievements",
      content: "recentHighScores"
    },
    {
      title: "Areas of Growth",
      content: "improvementAreas"
    },
    {
      title: "Upcoming Assessments",
      content: "futureAssignments"
    },
    {
      title: "Home Support Suggestions",
      content: "parentActionItems"
    }
  ]
};
```

### E. Export to NHA Gradebook
```javascript
function exportToNHA(studentId, reportingPeriod) {
  // Convert SBG proficiency to traditional grades
  const conversionScale = {
    4: 95,  // Advanced
    3: 85,  // Proficient
    2: 75,  // Developing
    1: 65   // Beginning
  };
  
  // Group by measurement topics
  const mtAverages = calculateMTAverages(studentId);
  
  // Generate traditional grade
  const overallGrade = weightedAverage(mtAverages);
  
  return {
    studentId,
    period: reportingPeriod,
    grade: overallGrade,
    breakdown: mtAverages,
    exportDate: new Date()
  };
}
```

---

## 4. User Interface Components

### Main Dashboard
```
┌─────────────────────────────────────────┐
│  SBG Tracker - PSCA 8th Grade ELA      │
├─────────────────────────────────────────┤
│ [Classes] [Standards] [Reports] [Setup] │
├─────────────────────────────────────────┤
│  Quick Actions:                         │
│  ○ Enter Grades                        │
│  ○ View Mastery Grid                   │
│  ○ Schedule Retake                     │
│  ○ Generate Parent Report              │
│  ○ Export to NHA                       │
└─────────────────────────────────────────┘
```

### Grade Entry Screen
```
┌─────────────────────────────────────────┐
│  Assignment: [Dropdown]                 │
│  Date: [Date Picker]                    │
├─────────────────────────────────────────┤
│  Standards Assessed:                    │
│  ☑ RL.8.2 (Primary)                    │
│  ☑ RL.8.3 (Primary)                    │
│  ☐ W.8.9 (Additional)                  │
├─────────────────────────────────────────┤
│  Student Grid:                          │
│  Name        | RL.8.2 | RL.8.3 | Notes │
│  Smith, J    |   3    |   4    | [+]   │
│  Jones, M    |   2    |   3    | [+]   │
├─────────────────────────────────────────┤
│  [Save] [Save & Next] [Cancel]         │
└─────────────────────────────────────────┘
```

### Student Mastery View
```
┌─────────────────────────────────────────┐
│  Student: [Name]  Course: [Gen Ed/8-9]  │
├─────────────────────────────────────────┤
│  Measurement Topics:                    │
│  MT1: ████████░░ 3.2/4.0               │
│  MT2: ██████░░░░ 2.8/4.0               │
│  MT3: █████████░ 3.5/4.0               │
│  MT4: ███████░░░ 3.0/4.0               │
│  MT5: ████████░░ 3.3/4.0               │
├─────────────────────────────────────────┤
│  Recent Assessments | Retakes Available │
│  Growth Trajectory  | Parent View       │
└─────────────────────────────────────────┘
```

---

## 5. Technology Stack Recommendations

### Option 1: Web Application (Recommended)
- **Frontend**: React with TypeScript
- **State Management**: Redux Toolkit
- **UI Framework**: Material-UI or Ant Design
- **Charts**: Recharts or Chart.js
- **Backend**: Node.js with Express
- **Database**: PostgreSQL with Prisma ORM
- **Authentication**: Auth0 or Firebase Auth
- **Hosting**: Vercel/Netlify (frontend) + Railway/Render (backend)

### Option 2: Desktop Application
- **Framework**: Electron with React
- **Database**: SQLite (local storage)
- **Sync**: Optional cloud sync with Firebase

### Option 3: Progressive Web App
- **Framework**: Next.js
- **Database**: Supabase (PostgreSQL)
- **Offline**: Service Workers for offline functionality
- **Export**: PDF generation with jsPDF

---

## 6. Implementation Timeline

### Phase 1: Core Setup (Week 1-2)
- Set up database schema
- Import standards and measurement topics
- Create student roster management
- Build basic grade entry interface

### Phase 2: Grading Features (Week 3-4)
- Implement mastery calculation
- Add retake tracking
- Create assignment management
- Build standards alignment tools

### Phase 3: Visualization (Week 5-6)
- Develop mastery grid view
- Create progress charts
- Build measurement topic dashboard
- Add trend analysis

### Phase 4: Communication (Week 7)
- Generate parent reports
- Create conference prep tools
- Build export to NHA function
- Add email notifications

### Phase 5: Polish & Testing (Week 8)
- User acceptance testing
- Performance optimization
- Documentation
- Training materials

---

## 7. Data Migration from Existing Systems

### Import Templates
```csv
// students.csv
student_id,first_name,last_name,email,course,period
12345,John,Smith,jsmith@psca.edu,Gen Ed 8th ELA,1

// grades.csv
student_id,assignment,standard,proficiency,date
12345,Unit 1 Test,RL.8.1,3,2024-09-15
```

---

## 8. Claude Code Implementation Instructions

When building this with Claude Code:

1. **Start with the database schema** - Create all tables with proper relationships
2. **Seed initial data** - Standards, measurement topics, and units
3. **Build CRUD operations** - Students, assignments, grades
4. **Implement business logic** - Mastery calculations, retake rules
5. **Create UI components** - Grade entry, mastery views, reports
6. **Add visualizations** - Charts and progress tracking
7. **Build export functionality** - NHA gradebook format, parent reports
8. **Test with sample data** - Use realistic scenarios from your curriculum

### Sample Claude Code Command:
```bash
claude-code "Create a Standards-Based Grading application for 8th grade ELA 
following the schema in sbg-grading-schema.md. Start with PostgreSQL database 
setup, then build a React frontend with grade entry and mastery tracking features. 
Include visualizations for student progress and parent communication tools."
```

---

This comprehensive schema aligns with your specific curriculum needs and SBG philosophy while addressing the limitations of the NHA gradebook system. The structure supports your goals of tracking mastery rather than averaging, managing retakes effectively, and providing clear communication to parents and students.