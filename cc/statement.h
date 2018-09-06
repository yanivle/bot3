#ifndef STATEMENT_H
#define STATEMENT_H

#include <string>
#include <vector>

// TODO: support other types of statements, not just eq (e.g. neq).
struct Statement {
  std::string var;
  std::string val;
  float p;

  Statement(const std::string& var, const std::string& val, float p=1.0):
  var(var), val(val), p(p) {}

  bool isConsistentWith(const Statement& other) {
    if (var != other.var) return true;
    if (val == other.val) return true;
    if (val == '*' || other.val == '*') return true;
  }
};

struct StatementList {
  vector<Statement> statements;

  bool isConsistentWith(const Statement& statement) {
    for (auto i = statements.begin(); i != statements.end(); ++i) {
      if (!i->isConsistentWith(statement)) {
        return false;
      }
    }
    return true;
  }

  bool satisfies(const Statement& statement) {

  }
};

#endif
