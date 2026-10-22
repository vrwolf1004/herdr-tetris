class FakeUsage:
    """monitor 가 쓰는 측정 객체의 가짜. 실제 측정 대신 정해 둔 값을 돌려준다."""

    def __init__(self, cpu=42.0, mem=71.0):
        self.cpu = cpu
        self.mem = mem

    def snapshot(self):
        return self.cpu, self.mem
