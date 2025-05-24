from odoo import fields, models, api

class ResUsers(models.Model):
    _inherit = 'res.users'
    
    branch_id = fields.Many2one('khabir.hijama.model', string='Branch')


    @api.model
    def create(self, vals):
        user = super().create(vals)
        user._update_branch_group()
        return user

    def write(self, vals):
        res = super().write(vals)
        self._update_branch_group()
        return res

    def _update_branch_group(self):
        branch_group = self.env.ref('khabir_hijama.group_branch_user')
        for user in self:
            if user.branch_id:
                user.groups_id |= branch_group
            else:
                user.groups_id -= branch_group
