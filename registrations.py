# Each cosmic pi client can register with the server
# We check package sequence numbers, hardware status

class Registrations(object):
    def __init__(self):

        self.reg = {"Ipa": "s", "Sqn": 0, "Pat": "s", "Ntf": False, "Htu": "0", "Bmp": "0", "Acl": "0", "Mag": "0"}
        self.regs = []

    def get_len(self):
        return len(self.regs)

    def get_index_by_value(self, knam, kval):
        if self.reg.has_key(knam):
            for i in range(0, len(self.regs)):
                if self.regs[i][knam] == kval:
                    return i
        return False

    def get_reg_by_value(self, knam, kval):
        if self.reg.has_key(knam):
            for i in range(0, len(self.regs)):
                if self.regs[i][knam] == kval:
                    return self.regs[i]
        return False

    def get_reg_by_index(self, indx):
        if indx in range(0, len(self.regs)):
            return self.regs[indx]

        return False

    def get_create_reg(self, knam, kval):
        r = self.get_reg_by_value(knam, kval)
        if r == False:
            i = len(self.regs)
            self.regs.append(self.reg.copy())
            self.regs[i][knam] = kval
            return self.regs[i]
        else:
            return r

    def set_reg(self, r):
        i = self.get_index_by_value("Ipa", r["Ipa"])
        if i == False:
            return False
        self.regs[i] = r.copy()
        return True