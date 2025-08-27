# Retrospective Process
*Built-in reflection and continuous improvement for development practices*

## 🔄 **When to Conduct Retrospectives**

### **Mandatory Retrospectives**
- After completing security-critical work
- After resolving major bugs or issues  
- After implementing complex features (>5 files changed)
- After any process violation or "rushed" development

### **Optional Retrospectives**
- Weekly development sessions
- After trying new tools or approaches
- When encountering repeated patterns of issues

## 📋 **Retrospective Analysis Framework**

### **Phase 1: What Happened? (Facts)**
```
📊 SESSION METRICS
- Time spent on task: ___
- Files modified: ___
- Tests added/modified: ___  
- Process violations: ___
- TodoWrite tasks completed: ___
```

### **Phase 2: What Went Well? (Successes)**
```
✅ SUCCESSES
- Processes that worked effectively
- Tools that provided value
- Decisions that led to good outcomes
- Quality measures that caught issues
```

### **Phase 3: What Went Wrong? (Problems)**
```
❌ PROBLEMS
- Process violations and why they occurred
- Tools that didn't work as expected
- Decisions that caused issues
- Quality gaps that allowed problems through
```

### **Phase 4: Why Did It Happen? (Root Causes)**
```
🔍 ROOT CAUSE ANALYSIS
For each problem identified:
- What was the immediate trigger?
- What underlying factors contributed?
- What could have prevented this?
- What early warning signs were missed?
```

### **Phase 5: What Should Change? (Improvements)**
```
🚀 IMPROVEMENT ACTIONS
- Process changes to prevent recurrence
- Tool improvements or additions needed
- Documentation updates required
- Training or knowledge gaps to address
```

## 🎯 **Retrospective Question Prompts**

### **Process Effectiveness**
- Did I follow the Ways of Working consistently?
- Which steps did I skip and why?
- What would have happened if I'd followed the process fully?
- Where did the process slow me down unnecessarily?

### **Quality and Security**
- Did I write tests before implementation?
- How did I verify the solution was secure?
- What could an attacker do with my implementation?
- Did I validate all assumptions I made?

### **Tools and Techniques**
- Which tools provided the most value?
- What searches or commands should I remember?
- What patterns should I reuse in the future?
- What debugging techniques were most effective?

### **Decision Making**
- What decisions did I make under time pressure?
- Which assumptions turned out to be wrong?
- When did I choose complex solutions over simple ones?
- What information was I missing when making key decisions?

## 📝 **Improvement Action Types**

### **Immediate Actions (This Session)**
- Fix any remaining issues identified
- Update documentation with lessons learned
- Add missing tests or validation
- Clean up any technical debt created

### **Process Updates (Next Session)**
- Update Ways of Working documents
- Add new checklist items
- Create new templates or utilities
- Enhance CLAUDE.md with lessons learned

### **Strategic Changes (Ongoing)**  
- Tool adoption or replacement
- Skill development priorities
- Architecture or design improvements
- Team communication enhancements

## 🔄 **Continuous Improvement Loop**

```
1. DO WORK
   ↓
2. REFLECT (Retrospective)
   ↓  
3. LEARN (Root cause analysis)
   ↓
4. IMPROVE (Update processes)
   ↓
5. APPLY (Use improved processes)
   ↓
Back to step 1
```

## 📋 **Retrospective Checklist**

After any significant work session:

- [ ] **Conduct retrospective analysis** (10-15 minutes)
- [ ] **Identify 1-3 key lessons learned**
- [ ] **Update relevant documentation** with insights
- [ ] **Plan 1-2 concrete improvements** for next session
- [ ] **Update CLAUDE.md** with any new patterns or approaches

*This retrospective process ensures continuous learning and process improvement.*