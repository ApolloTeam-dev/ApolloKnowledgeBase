// Toolchain smoke test: C++ compiler.
class Counter {
public:
    Counter() : n(0) {}
    void add(int v) { n += v; }
    int value() const { return n; }
private:
    int n;
};

int smoke_cpp(int v)
{
    Counter c;
    c.add(v);
    return c.value();
}
